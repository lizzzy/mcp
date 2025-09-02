from openai import OpenAI
import asyncio
import json
import sys
import os
from mcp.client.sse import sse_client
from mcp import ClientSession
from contextlib import AsyncExitStack
from dotenv import load_dotenv
load_dotenv()

class MCPClient:
    def __init__(self, server_path):
        self.openai = OpenAI(
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),
            timeout=60,
        )
        self.exit_stack = AsyncExitStack()
        self.resources = {}  # 存储服务端资源信息

    async def run(self, query: str):
        # 1.创建read_stream, write_stream数据读写流
        read_stream, write_stream = await self.exit_stack.enter_async_context(
            sse_client("http://127.0.0.1:8000/sse")
        )
        # 2. 创建session，指定具体类型对象，方便后续进行代码补全识别
        session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream=read_stream, write_stream=write_stream)
        )
        # 3. 初始化
        await session.initialize()
        # 4. 获取服务端提供的所有资源
        functions = []
        responses = (await session.list_resources()).resources
        # print(responses)
        for resource in responses:
            uri = resource.uri
            name = resource.name
            description = resource.description
            mime_type = resource.mimeType

            self.resources[name] = {
                "uri": uri,
                "name": name,
                "description": description,
                "mime_type": mime_type,
            }
            # 将资源转化为大模型能够调用的形式（Function Calling），新建functions列表，用于存放数据

            functions.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        # 资源中没有input_schema信息，为保持一致，设置为None
                        "input_shema": None,
                    },
                }
            )

        # 创建消息发送给LLM
        messages = [{"role": "user", "content": query}]
        openai_response = self.openai.chat.completions.create(
            messages=messages, model="gpt-4o", tools=functions
        )

        model_choice = openai_response.choices[0]
        # 如果LLM的回复是tool_calls，执行调用工具代码
        if model_choice.finish_reason == "tool_calls":
            # 为了让LLM能够更加精准的回复，需要将LLM返回的message也添加到messages中
            model_messages = model_choice.message
            # message.model_dump: pydantic库提供的方法，model_message是oydantic的BaseModel子类对象
            # model_dump是将Model对象上的属性转换为字典
            messages.append(model_messages.model_dump())

            tool_calls = model_messages.tool_calls
            for tool_call in tool_calls:
                tool_call_id = tool_call.id
                function = tool_call.function
                function_arguments = function.arguments
                function_name = function.name
                uri = self.resources[function_name]["uri"]
                # 执行调用，responses是服务端返回
                response = await session.read_resource(uri)
                # print(response)
                result = response.contents[0].text
                # 把result传给LLM，让LLM生成最终结果
                messages.append({
                    "role":"tool",
                    "content":result,
                    "tool_call_id":tool_call_id
                })
                model_response = self.openai.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                print(model_response.choices[0].message.content)


    async def aclose(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPClient(server_path="./server.py")
    try:
        await client.run("查询上海海事大学的信息")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
