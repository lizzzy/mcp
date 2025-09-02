import asyncio
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import RequestParams

mcp: FastMCP = FastMCP()


@mcp.tool()
async def log_tool(files: list[str], ctx: Context):
    """
    日志输出
    处理多个文件进行进度汇报
    :param files: 多个文件路径
    :param ctx: 上下文对象，无需客户端传递
    :return: 处理结果
    """
    for index, file in enumerate(files):
        await asyncio.sleep(1)
        """
        查看ctx.report_progress()函数文档，这个函数有一个progress_token参数
        progress_token = self.request_context.meta.progressToken if self.request_context.meta else None
        if progress_token is None: return
        如果这个参数的赋值为None，调用函数直接返回为空，相当于函数不会发送消息
        要求函数发送消息，则要求progress_token参数不能为None
        self.request_context.meta不为None，返回self.request_context.meta.progressToken
        ProgressToken = str | int 需要指定为字符串或整型数据避免None
        这里使用每一个请求的id
        """
        ctx.request_context.meta = RequestParams.Meta(progressToken=ctx.request_id)
        await ctx.report_progress(index, len(files))
    return "处理完毕"


if __name__ == "__main__":
    mcp.run(transport="sse")
