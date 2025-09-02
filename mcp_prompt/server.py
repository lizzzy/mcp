from mcp.server.fastmcp import FastMCP

app = FastMCP()


@app.prompt()
def policy_prompt(policy: str):
	'''
    能够对用户提供的政策内容，对其进行总结、提取关键信息的提示词模板
    :param policy: 需要总结的政策内容
    :return: 总结政策的提示词模板
    '''
	# 如果直接返回一个字符串，那么哭护短接收到的是一个PromptMessage对象
	# 这个对象默认role=user，可以是其他role
    # 如[{"role":"stystem", "content":"xxx"}] 必须是字典形式
	return [{
		"role":"user",
		"content":f'''
		这个是政策内容:“{policy}”，请对该政策内容进行总结，总结的规则为:
        1.提取政策要点。
        2.针对每个政策要点按照以下格式进行总结
            *要点标题:政策的标题，要包含具体的政策信息
            *针对人群:政策针对的人群
            *有效时间:政策执行的开始时间和结束时间
            *相关部门:政策是由哪些部门执行总结的内容不要太官方，用通俗易懂的语言。
		'''
	}]

if __name__ == "__main__":
    app.run(transport="sse")
