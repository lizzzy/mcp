from openai import OpenAI
import asyncio
import json
import sys
import os
from mcp.client.stdio import StdioServerParameters,stdio_client
from mcp import ClientSession
from contextlib import AsyncExitStack
from dotenv import load_dotenv
load_dotenv()
class MCPClient:
  def __init__(self, server_path):
    self.server_path = server_path
    self.openai = OpenAI(
      base_url=os.getenv("BASE_URL"),
      api_key=os.getenv("API_KEY"),
      timeout=60,
    )
    self.exit_stack = AsyncExitStack()

  async def run(self, query: str):
    # 1. 创建连接服务器端的参数
    from mcp.client.stdio import StdioServerParameters
    server_parameters = StdioServerParameters(
      command = 'python',
      args = [self.server_path],
    )

    # # 2. 创建读写流
    # async with stdio_client(server=server_parameters) as (read_stream, write_stream):
    #   # 3. 创建客户端与服务端的进程通话
    #   async with ClientSession(read_stream, write_stream) as session:
    #     # 4. 初始化请求
    #     await session.initialize()
    #     # 5. 获取服务端的所有tools
    #     response = await session.list_tools()
    #     # print(response)

    #     # 6. 将工具封装成Function Calling能识别的对象
    #     tools = []
    #     for tool in response.tools:
    #       name = tool.name
    #       description = tool.description
    #       input_shema = tool.inputSchema
    #       tools.append({
    #         "type": "function",
    #         "function": {
    #           "name": name,
    #           "description": description,
    #           "input_shema": input_shema,
    #         }
    #       })
    #     # print(tools)

    #     # 7. 发送消息给LLM，让LLM选择调用哪个工具
    #     # role：
    #     # 1. user：用户发送给大模型的消息
    #     # 2. assistant：大模型发给用户的消息
    #     # 3. system：给大模型的系统提示词
    #     # 4. tool：函数执行完后返回的信息
    #     messages = [{
    #       "role": "user",
    #       "content": query
    #     }]
    #     openai_response = self.openai.chat.completions.create(
    #       messages=messages,
    #       model="gpt-4o",
    #       tools = tools
    #     )
    #     # print(openai_response)

    #     # ChatCompletion(id='chatcmpl-C8jallhbLIliYD3YyA0mcAf1YQBlj', choices=[Choice(finish_reason='tool_calls', index=0, logprobs=None, message=ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_h8J6DJCyzio9fAwZP1Ogpeby', function=Function(arguments='{"a":3,"b":5}', name='plus_tool'), type='function')]))], created=1756197915, model='gpt-4o-2024-08-06', object='chat.completion', service_tier='default', system_fingerprint='fp_ea40d5097a', usage=CompletionUsage(completion_tokens=18, prompt_tokens=75, total_tokens=93, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))

    #     choice = openai_response.choices[0]
    #     # 如果finish_reason 为tool_calls，说明LLM选择了一个工具
    #     if choice.finish_reason == 'tool_calls':
    #       # 为了LLM能够更加精准回复，将LLM选择的工具message，重新添加到messages
    #       messages.append(choice.message.model_dump())
    #       # 获取工具
    #       tool_calls = choice.message.tool_calls
    #       # 依次调用
    #       for tool_call in tool_calls:
    #         tool_call_id = tool_call.id
    #         function = tool_call.function
    #         function_name = function.name
    #         function_arguments = json.loads(function.arguments)
    #         result = await session.call_tool(name = function_name, arguments=function_arguments)
    #         content = result.content[0].text
    #         print(content)
    #         messages.append({
    #           "role": "tool",
    #           "content": content,
    #           "tool_call_id": tool_call_id
    #         })

    #     # 重新把数据发给LLM，让LLM给出最终响应
    #     response = self.openai.chat.completions.create(
    #       model = "gpt-4o",
    #       messages = messages
    #     )
    #     print(response.choices[0].message.content)

    # 改成用异步上下文堆栈来处理
    read_stream, write_stream = await self.exit_stack.enter_async_context(stdio_client(server=server_parameters))
    session = await self.exit_stack.enter_async_context(ClientSession(read_stream=read_stream, write_stream=write_stream))

    # 4. 初始化请求
    await session.initialize()
    # 5. 获取服务端的所有tools
    response = await session.list_tools()
    # print(response)

    # 6. 将工具封装成Function Calling能识别的对象
    tools = []
    for tool in response.tools:
      name = tool.name
      description = tool.description
      input_shema = tool.inputSchema
      tools.append({
        "type": "function",
        "function": {
          "name": name,
          "description": description,
          "input_shema": input_shema,
        }
      })
    # print(tools)

    # 7. 发送消息给LLM，让LLM选择调用哪个工具
    # role：
    # 1. user：用户发送给大模型的消息
    # 2. assistant：大模型发给用户的消息
    # 3. system：给大模型的系统提示词
    # 4. tool：函数执行完后返回的信息
    messages = [{
      "role": "user",
      "content": query
    }]
    openai_response = self.openai.chat.completions.create(
      messages=messages,
      model="gpt-4o",
      tools = tools
    )
    # print(openai_response)

    # ChatCompletion(id='chatcmpl-C8jallhbLIliYD3YyA0mcAf1YQBlj', choices=[Choice(finish_reason='tool_calls', index=0, logprobs=None, message=ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_h8J6DJCyzio9fAwZP1Ogpeby', function=Function(arguments='{"a":3,"b":5}', name='plus_tool'), type='function')]))], created=1756197915, model='gpt-4o-2024-08-06', object='chat.completion', service_tier='default', system_fingerprint='fp_ea40d5097a', usage=CompletionUsage(completion_tokens=18, prompt_tokens=75, total_tokens=93, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))

    choice = openai_response.choices[0]
    # 如果finish_reason 为tool_calls，说明LLM选择了一个工具
    if choice.finish_reason == 'tool_calls':
      # 为了LLM能够更加精准回复，将LLM选择的工具message，重新添加到messages
      messages.append(choice.message.model_dump())
      # 获取工具
      tool_calls = choice.message.tool_calls
      # 依次调用
      for tool_call in tool_calls:
        tool_call_id = tool_call.id
        function = tool_call.function
        function_name = function.name
        function_arguments = json.loads(function.arguments)
        result = await session.call_tool(name = function_name, arguments=function_arguments)
        content = result.content[0].text
        print(content)
        messages.append({
          "role": "tool",
          "content": content,
          "tool_call_id": tool_call_id
        })
      # 重新把数据发给LLM，让LLM给出最终响应
      response = self.openai.chat.completions.create(
        model = "gpt-4o",
        messages = messages
      )
      print(response.choices[0].message.content)

    else:
      print('回复错误')

  async def aclose(self):
    await self.exit_stack.aclose()

async def main():
  client = MCPClient(server_path='./server.py')
  try:
    await client.run('计算1加0.00001等于多少')
  finally:
    await client.aclose()

if __name__ == '__main__':
  # client = MCPClient('./server.py')
  # asyncio.run(client.run('计算1加0.00001等于多少'))
  asyncio.run(main())
