import aiofiles
import asyncio
import base64
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
        resources = (await session.list_resources()).resources
        # print(responses)
        for resource in resources:
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
                        "input_schema": None,
                    },
                }
            )

        # 创建消息发送给LLM
        messages = [
            {"role": "system", "content": "你有能力通过工具 Avatar获取头像"},
            {"role": "user", "content": query},
        ]
        openai_response = self.openai.chat.completions.create(
            messages=messages, model="gpt-4o", tools=functions
        )

        choice = openai_response.choices[0]
        # print(choice)
        if choice.finish_reason == "tool_calls":
            tool_call = choice.message.tool_calls[0]
            function = tool_call.function
            function_name = function.name
            function_uri = self.resources[function_name]["uri"]
            result = await session.read_resource(function_uri)
            print(result)
            async with aiofiles.open("data/avatar.png", mode="wb") as fp:
                await fp.write(base64.b64decode(result.contents[0].blob))
            print("下载完毕")

    async def aclose(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPClient(server_path="./server_img.py")
    try:
        await client.run("请调用工具获取一张用户头像")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
