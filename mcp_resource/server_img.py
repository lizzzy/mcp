import aiofiles
from mcp.server.fastmcp import FastMCP

app = FastMCP()


@app.resource(
    uri="image://avatar.png",
    name="avatar",
    description="获取用户头像",
    mime_type="image/png",
)
async def Avatar():
    # 打开文件获取数据，采用异步方法处理
    async with aiofiles.open(
        "C:/Users/LT01/Desktop/Doc/IMG/avatar.png", mode="rb"
    ) as fp:
        content = await fp.read()
    return content


if __name__ == "__main__":
    app.run(transport="sse")
