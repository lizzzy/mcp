import aiofiles
from mcp.server.fastmcp import FastMCP

app = FastMCP()


@app.resource(
    uri="user://{user_id}",
    name="useer_detail",
    description="根据参数user_id，返回用户详细信息。\n :param user_id: 用户id",
    mime_type="application/json",
)
async def user_detail(user_id: str):
    return {
        "user_id": user_id,
        "username": "张三",
        "gender": "male",
        "university": "北京大学",
    }


if __name__ == "__main__":
    app.run(transport="sse")
