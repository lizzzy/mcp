import json
import os
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class MCPClient:
    def __init__(self):
        # 初始化会话和客户端对象
        self.session: Optional[ClientSession] = None # 用于保存 MCP 客户端会话
        self.exit_stack = AsyncExitStack()  # 用于管理异步资源的生命周期
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),  # 从环境变量中获取 API 密钥
        )

    async def connect_to_server(self, server_script_path: str):
        """
        连接到 MCP 服务器

        参数:
            server_script_path: 服务器脚本路径 (.py 或 .js)
        """

        is_python = server_script_path.endswith('.py')  # 判断是否为 Python 脚本
        is_js = server_script_path.endswith('.js') # 判断是否为 JavaScript 脚本
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node" # 根据文件类型选择执行命令
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        # 启动标准输入输出客户端
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        # 创建并初始化 MCP 客户端会话
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize() # 初始化会话

        # 列出可用工具
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools]) # 打印可用工具名称

    async def process_query(self, query: str) -> str:
        """处理用户查询，使用 LLM 和可用工具进行响应"""

        messages = [
            {
                "role": "user",
                "content": query # 用户输入的查询内容
            }
        ]

        # 获取可用工具列表并构造工具调用格式
        response = await self.session.list_tools()
        available_tools =[
            {
                "type": "function",
                "function": {
                    "name":tool.name, # 工具名称
                    "description": tool.description,  # 工具描述
                    "parameters": tool.inputSchema # 输入参数格式
                }
            }
        for tool in response.tools]

        # 调用 LLM 模型生成回复
        response = self.client.chat.completions.create(
            model=os.getenv("MODEL"),  # 使用的模型名称
            messages=messages, # 对话历史
            tools=available_tools # 可用工具列表
        )

        # 处理模型回复并执行工具调用（如有）
        tool_results = []
        final_text = []

        for choice in response.choices:
            message = choice.message
            is_function_call = message.tool_calls

            if is_function_call:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # 执行工具调用
                result = await self.session.call_tool(tool_name, tool_args)
                tool_results.append({"call": tool_name, "result": result})
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")  # 记录调用信息

                # 将工具调用结果加入对话历史
                if message.content and hasattr(message.content, 'text'):
                    messages.append({
                        "role": "assistant",
                        "content": message.content
                    })

                messages.append({
                    "role": "user",
                    "content": result.content[0].text
                })

                # 再次调用 LLM 获取最终回复
                response = self.client.chat.completions.create(
                    model=os.getenv("MODEL"),
                    messages=messages,
                )
                final_text.append(response.choices[0].message.content) # 添加模型最终回复
            else:
                final_text.append(message.content) # 直接添加模型回复

        return "\n".join(final_text)  # 返回最终回复内容

    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip() # 获取用户输入

                if query.lower() == 'quit': # 如果输入 quit 则退出循环
                    break

                response = await self.process_query(query)  # 处理用户查询
                print("\n" + response) # 打印回复

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()  # 关闭所有异步资源


async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_server_script>")
        sys.exit(1)

    # 创建 MCP 客户端
    client = MCPClient()
    try:
        # 将客户端链接到 MCP Server
        await client.connect_to_server(sys.argv[1])
        # 开启聊天循环
        await client.chat_loop()
    finally:
        # 程序终止，清理资源
        await client.cleanup()


if __name__ == "__main__":
    import sys
    # 异步运行主函数
    asyncio.run(main())
