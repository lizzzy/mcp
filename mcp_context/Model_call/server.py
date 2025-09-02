from mcp.server.fastmcp import FastMCP, Context
from mcp.types import SamplingMessage, TextContent

mcp: FastMCP = FastMCP()


@mcp.tool()
async def sampling_tool(ctx: Context):
    """
    模型调用
    直接发送一个Sampling的消息
    """
    response = await ctx.session.create_message(
        max_tokens=2048,
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text", text="请帮我按照主题“2025年高考”为主题写两篇诗词"
                ),
            )
        ],
    )
    print(response)
    return "采样完成"


if __name__ == "__main__":
    mcp.run(transport="sse")
