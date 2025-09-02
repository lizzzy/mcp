from mcp.server.fastmcp import FastMCP

app = FastMCP("start mcp")

@app.tool()
def plus_tool(a:float, b:float) -> float:
  '''
  计算两个浮点数和
  :param a: 浮点数1
  :param b: 浮点数2
  :return 浮点数
  '''
  # 动态获取自身schema信息
  try:
      from pprint import pprint
      # FastMCP 可能将工具注册在 app._tools 或 app.tools
      # 取第一个名为 plus_tool 的schema
      schema = None
      if hasattr(app, "_tools"):
          for t in app._tools:
              if t.name == "plus_tool":
                  schema = t.input_schema if hasattr(t, "input_schema") else t.__dict__
                  break
      elif hasattr(app, "tools"):
          for t in app.tools:
              if t.name == "plus_tool":
                  schema = t.input_schema if hasattr(t, "input_schema") else t.__dict__
                  break
      print("plus_tool schema info:")
      pprint(schema)
  except Exception as e:
      print(f"schema info error: {e}")
  return a + b

if __name__ == '__main__':
  # 工具注册后，保存 plus_tool 的 schema 信息到日志
  try:
      from pprint import pprint
      print("app._tools:")
      if hasattr(app, "_tools"):
          pprint(app._tools)
      print("app.tools:")
      if hasattr(app, "tools"):
          pprint(app.tools)
  except Exception as e:
      print(f"print tools error: {e}")
  # app.run(transport='stdio')
  app.run(transport='sse')
