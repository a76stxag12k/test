from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun

# Web検索ツールの定義
wrapper = DuckDuckGoSearchAPIWrapper(max_results=25)
web_search_tool = DuckDuckGoSearchRun(api_wrapper=wrapper)

# テスト実行
test_response = web_search_tool.invoke("今のワシントンの天気は？")
print(test_response)
