from openai import OpenAI
import asyncio
import os
import json
from mcp.client.sse import sse_client
from mcp import ClientSession
from contextlib import AsyncExitStack
from dotenv import load_dotenv

load_dotenv()


class MCPClient:
    def __init__(self, server_path):
        self.openai = OpenAI(
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),
            timeout=60,
        )
        self.exit_stack = AsyncExitStack()
        self.prompts = {}  # 存储服务端prompts

    async def run(self, query: str):
        read_stream, write_stream = await self.exit_stack.enter_async_context(
            sse_client("http://127.0.0.1:8000/sse")
        )
        session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream=read_stream, write_stream=write_stream)
        )
        # 3. 初始化
        await session.initialize()
        # 4. 获取服务端所有提示词
        functions = []
        prompts = (await session.list_prompts()).prompts
        # print(prompts)

        for prompt in prompts:
            name = prompt.name
            description = prompt.description
            prompt_arguments = prompt.arguments
            '''
            在进行遍历循环时候，获取信息是针对具体的sesiion会话的读取服务端的需求
            - Tool中是session.call_tool(name=function_name, arguments=function_arguments).即需要获取名称和参数
            - Resource中是session.read_resource(uri)，需要获取uri，而uri是在所有资源列表中，可以通过名称访问，所以在类对象初始化时候创建了一个self.resources容器存放资源信息。
            - Resource Templatez中也是session.read_resource(uri)，和前面一样
            - Prompt中是session.get_prompt(name=function_name,arguments=function_arguments).即需要获取名称和参数

            self.prompts[name]没起效，用于扩展如：
            本地缓存：将提示词信息缓存在客户端，避免每次都向服务器请求。
            本地验证：在将请求发送给 LLM 之前，先在本地验证工具调用的参数是否正确。
            UI 显示：在一个用户界面中，向用户展示所有可用的提示词（工具）。
            '''
            self.prompts[name] = {
                "name": name,
                "description": description,
                "arguments": prompt_arguments,
            }
            functions.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "input_schema": None,
                    },
                }
            )

            # 消息发送LLM
            messages = [{"role": "user", "content": query}]
            openai_response = self.openai.chat.completions.create(
                messages=messages, model="gpt-4o", tools=functions
            )
            # print(openai_response.choices[0].message.tool_calls[0].function)
            choice = openai_response.choices[0]
            if choice.finish_reason == "tool_calls":
                # LLM选择tool的message添加到messages中
                # messages中已经包含一个工具选择的message
                messages.append(choice.message.model_dump())

                tool_call = choice.message.tool_calls[0]
                function = tool_call.function
                function_name = function.name
                function_arguments = json.loads(function.arguments)
                if function_name == "policy_prompt":
                    with open("data/policy.txt", mode="r", encoding="utf-8") as f:
                        policy = f.read()
                    function_arguments["policy"] = policy
                result = await session.get_prompt(
                    name=function_name, arguments=function_arguments
                )
                # print(result)
                content = result.messages[0].content.text
                messages.append(
                    {"role": "tool", "content": content, "tool_call_id": tool_call.id}
                )
                '''
                为什么要传入 tool_call_id？
                1. __第一次 API 调用__：我们向 LLM 发送一个用户查询和一系列可用的工具。
                2. __LLM 的回应__：如果 LLM 决定使用一个工具，它不会直接返回最终答案，而是会返回一个 `tool_calls` 对象。这个对象里包含了它想要调用的函数名、参数，以及一个独一无二的 `tool_call_id`。这个 ID 就像是这次工具调用请求的“凭证”或“编号”。
                3. __客户端执行工具__：我们的客户端代码（`client.py`）接收到这个 `tool_calls` 对象后，根据其中的信息去调用 MCP 服务器，获取提示词的执行结果（也就是 `content`）。
                4. __第二次 API 调用__：为了让 LLM 基于工具的执行结果生成最终的用户回答，我们需要进行第二次 API 调用。在这次调用中，我们需要将工具的执行结果 `content` 发回给 LLM。同时，我们必须附上原始的 `tool_call_id`。
                5. __建立关联__：通过传入 `tool_call_id`，我们告诉 LLM：“这个 `content` 是对你之前那次编号为 `tool_call_id` 的工具调用请求的响应”。这样，LLM 就能将工具的输出和它之前的思考过程关联起来，从而生成连贯的、基于工具结果的最终答案。
                简单来说，`tool_call_id` 是为了在多次对话交互中，将工具的调用请求和其返回结果进行匹配，确保对话能够正确地进行下去。

                - 您的代码向 OpenAI 发送了初始请求和可用工具列表。
                - OpenAI 模型决定使用 `policy_prompt` 工具，并返回一个工具调用请求，这个请求中包含一个独一无二的 `tool_call_id`。
                - 您的代码执行了这个工具（通过 MCP 服务器），得到了总结内容 `content`。
                - 为了让 OpenAI 模型基于这个 `content` 生成最终的回答，您的代码需要将 `content` 发回给模型。此时，__必须附上原始的 `tool_call_id`__。
                '''
                # 将message发送给llm返回最终结果
                response = self.openai.chat.completions.create(
                    model="gpt-4o", messages=messages
                )
                print(response.choices[0].message.content)

    async def aclose(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPClient(server_path="./server.py")
    try:
        await client.run(f"帮我总结这个政策")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
