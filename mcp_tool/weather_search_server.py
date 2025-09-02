# import requests
from mcp.server.fastmcp import FastMCP
import httpx
from contextlib import AsyncExitStack

weather_api_key = "0e013475bc8c4876b4823959252708"
weather_base_url = "http://api.weatherapi.com/v1/current.json"

app = FastMCP()

@app.tool()
async def get_weather(city: str) :
    '''
    获取城市当前的天气信息
    :param city: 具体城市，需要拼音
    :return:
    '''
    params = {
        "key": weather_api_key,
        "q": city,
    }
    exit_stack = AsyncExitStack()
    client = await exit_stack.enter_async_context(httpx.AsyncClient())
    try:
        response = await client.get(weather_base_url, params=params)
        print(response.json())
        return response.json()
    except Exception as err:
        print(f"查询接口异常:{err}")
        return {"error": f"查询接口异常:{err}"}


    # with httpx.Client() as client:
    #     try:
    #         response = client.get(weather_base_url, params=params)
    #         print(response.json())
    #         return response.json()
    #     except Exception as err:
    #         print(f"查询接口异常:{err}")
    #         return {"error": f"查询接口异常:{err}"}

    # response = requests.get(weather_base_url, params=params)
    # print(response.json())
    # return response.json()   #需要以json的数据格式返回，客服端才可以解析


if __name__ == "__main__":
    app.run(transport='stdio')
