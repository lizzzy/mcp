import json

from mcp.server import FastMCP

# 准备模拟数据
# 用户信息数组，用户信息key是用户名，value是用户信息
users = {
    "alice": {"name": "Alice", "age": 25},
    "bob": {"name": "Bob", "age": 30},
    "charlie": {"name": "Charlie", "age": 35},
}

# 用户资源数组，用户资源key是用户名，value是资源内容
resources = {
    "alice": ["res1", "res2", "res3"],
    "bob": ["res4", "res5"],
    "charlie": ["res6"]
}

# 应用配置信息
config = {
    "app_name": "FastMCP",
    "app_version": "1.0.0",
    "app_description": "A FastMCP server",
    "app_author": "FastMCP Team",
    "app_license": "MIT",
    "app_url": "https://github.com/FastMCP/FastMCP",
    "app_contact": "https://github.com/FastMCP/FastMCP/issues",
    "app_email": "fastmcp@gmail.com",
}

mcp: FastMCP = FastMCP(
    name="这是FastMCP的参数name",
    instructions="""
    这是FastMCP的参数instructions.
    """
)


#             @server.tool()
#             def my_tool(x: int) -> str:
#                 return str(x)
#
#             @server.tool()
#             def tool_with_context(x: int, ctx: Context) -> str:
#                 ctx.info(f"Processing {x}")
#                 return str(x)
#
#             @server.tool()
#             async def async_tool(x: int, context: Context) -> str:
#                 await context.report_progress(50, 100)
#                 return str(x)
@mcp.tool()
def custom_tool(name: str) -> str:
    """
    获取指定用户的信息
    """
    key = name.lower()
    if key not in users:
        return json.dumps({"error": f"用户 {name} 不存在"})
    return json.dumps(users[key], ensure_ascii=False)


#             @server.resource("resource://my-resource")
#             def get_data() -> str:
#                 return "Hello, world!"
#
#             @server.resource("resource://my-resource")
#             async get_data() -> str:
#                 data = await fetch_data()
#                 return f"Hello, world! {data}"
#
#             @server.resource("resource://{city}/weather")
#             def get_weather(city: str) -> str:
#                 return f"Weather for {city}"
#
#             @server.resource("resource://{city}/weather")
#             async def get_weather(city: str) -> str:
#                 data = await fetch_weather(city)
#                 return f"Weather for {city}: {data}"
@mcp.resource("resource://{user_name}")
def custom_resource_template(user_name: str) -> str:
    """
    获取指定用户的资源列表
    """
    return json.dumps(resources[user_name])


@mcp.resource("config://app")
def custom_resource() -> str:
    """
    获取应用配置信息
    """
    # 将config转换成json字符串
    return json.dumps(config)


#             @server.prompt()
#             def analyze_table(table_name: str) -> list[Message]:
#                 schema = read_table_schema(table_name)
#                 return [
#                     {
#                         "role": "user",
#                         "content": f"Analyze this schema:\n{schema}"
#                     }
#                 ]
#
#             @server.prompt()
#             async def analyze_file(path: str) -> list[Message]:
#                 content = await read_file(path)
#                 return [
#                     {
#                         "role": "user",
#                         "content": {
#                             "type": "resource",
#                             "resource": {
#                                 "uri": f"file://{path}",
#                                 "text": content
#                             }
#                         }
#                     }
#                 ]
@mcp.prompt()
def custom_prompt(name: str) -> str:
    """
    欢迎指定用户
    """
    return f"欢迎，{name}！有什么需要帮助的码?"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run()
