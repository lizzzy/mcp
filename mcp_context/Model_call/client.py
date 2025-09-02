import asyncio
from openai import OpenAI
import os
from typing import Any
from mcp.client.sse import sse_client
from mcp import ClientSession
from mcp.types import CreateMessageRequestParams, TextContent, CreateMessageResult
from mcp.client.session import RequestResponder
from dotenv import load_dotenv

load_dotenv()


async def sampling_handler(
    context: RequestResponder["ClientSession", Any], params: CreateMessageRequestParams
):
    print(f"context: {context}")
    print(f"params: {params}")
    openai = OpenAI(
        base_url=os.getenv("BASE_URL"),
        api_key=os.getenv("API_KEY"),
        timeout=60,
    )
    message = params.messages[0]
    messages = [{"role": message.role, "content": message.content.text}]
    response = openai.chat.completions.create(messages=messages, model="gpt-4o")
    print(response)
    text = response.choices[0].message.content
    return CreateMessageResult(
        role="assistant",
        content=TextContent(type="text", text=text),
        model="gpt-4o",
    )


async def run():
    async with sse_client("http://127.0.0.1:8000/sse") as (read_stream, write_stream):
        async with ClientSession(
            read_stream, write_stream, sampling_callback=sampling_handler
        ) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            # print(tools)
            tool = tools[0]
            response = await session.call_tool(name=tool.name)
            print(response)


if __name__ == "__main__":
    asyncio.run(run())
