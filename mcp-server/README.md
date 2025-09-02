参考文档

```
https://blog.csdn.net/jeffray1991/article/details/147387894?ops_request_misc=elastic_search_misc&request_id=4b413142ae556d48060f72b04b569e03&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~ElasticSearch~search_v2-2-147387894-null-null.142^v102^pc_search_result_base9&utm_term=MCP%E4%BB%8E0%E5%88%B01&spm=1018.2226.3001.4187
```

python命令生成随机token

```python
python -c "import uuid; print(uuid.uuid4())"
```

启动：

```bash
$env:MCP_PROXY_TOKEN="57dd3b0e-3505-4466-906e-085dd231655f"
mcp dev main.py
```

http://127.0.0.1:6274/ 中 Configuration - Proxy Session Token写入随机token
