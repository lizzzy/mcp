import asyncio
import json
import os
from openai import OpenAI
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
        resources = (await session.list_resource_templates()).resourceTemplates
        # print(resources)

        for resource in resources:
            uri = resource.uriTemplate
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
                        "input_schema": None,
                    },
                }
            )

        # 创建消息发送给LLM
        messages = [
            {"role": "system", "content": "你有能力通过工具 user_detail获取用户信息"},
            {"role": "user", "content": query},
        ]
        openai_response = self.openai.chat.completions.create(
            messages=messages, model="gpt-4o", tools=functions
        )
        model_choice = openai_response.choices[0]
        # print(choice)
        if model_choice.finish_reason == "tool_calls":
            model_messages = model_choice.message
            messages.append(model_messages.model_dump())

            tool_calls = model_messages.tool_calls
            for tool_call in tool_calls:
                tool_call_id = tool_call.id
                function = tool_call.function
                # print(function)
                function_arguments = json.loads(function.arguments)
                function_name = function.name
                uri = self.resources[function_name]["uri"]
                # print(uri, type(uri))
                # print(function_arguments, type(function_arguments))
                response = await session.read_resource(uri.format(**function_arguments))
                # print(response)

                result = response.contents[0].text
                # 把result传给LLM，让LLM生成最终结果
                messages.append(
                    {"role": "tool", "content": result, "tool_call_id": tool_call_id}
                )
                model_response = self.openai.chat.completions.create(
                    model="gpt-4o", messages=messages
                )
                print(model_response.choices[0].message.content)

    async def aclose(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPClient(server_path="./server_template.py")
    try:
        await client.run("帮我查找一下用户id为111的用户信息")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
