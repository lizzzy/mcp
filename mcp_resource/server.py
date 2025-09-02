import aiofiles
from mcp.server.fastmcp import FastMCP

app = FastMCP()


@app.resource(
    uri="file://data/SMU.txt",
    name="SMU",
    description="获取上海海事大学的相关信息",
    mime_type="text/plain",
)
async def SMU_resource():
    async with aiofiles.open("data/SMU.txt", mode="r", encoding="utf-8") as fp:
        content = fp.read()
    return content


if __name__ == "__main__":
    app.run(transport="sse")
