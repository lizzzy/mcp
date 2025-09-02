import asyncio
from mcp.server.fastmcp import FastMCP, Context

mcp: FastMCP = FastMCP()


@mcp.tool()
async def log_tool(files: list[str], ctx: Context):
    """
    进度汇报
    处理文件的接口
    :param files: 文件列表
    :param ctx: 上下文对象，无需客户端传递
    :return: 处理结果
    """
    for index, file in enumerate(files):
        await asyncio.sleep(1)
        # ctx.log()
        await ctx.info(f"正在处理第{index+1}个文件")
    return "所有文件处理完成"


if __name__ == "__main__":
    mcp.run(transport="sse")
