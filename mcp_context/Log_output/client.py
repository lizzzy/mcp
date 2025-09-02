import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession
from mcp.types import LoggingMessageNotificationParams


async def logging_handler(params: LoggingMessageNotificationParams):
    print(params)


async def run():
    async with sse_client("http://127.0.0.1:8000/sse") as (read_stream, write_stream):
        async with ClientSession(
            read_stream, write_stream, logging_callback=logging_handler
        ) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            # print(tools)
            tool = tools[0]
            response = await session.call_tool(
                name=tool.name, arguments={"files": ["a.txt", "b.txt"]}
            )
            # print(response)


if __name__ == "__main__":
    asyncio.run(run())
