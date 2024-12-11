from langchain_community.chat_models import ChatOllama
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.prompts import PromptTemplate
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict
import requests
import json

API_SERVER_URL = "http://localhost:11434/api/chat"

# ルータープロンプトの定義
router_prompt = PromptTemplate(
    template="""  
    <|begin_of_text|>
    <|start_header_id|>system<|end_header_id|>
    あなたはユーザーの質問を適切にルーティングする専門家です。
    Web検索が必要か、それとも直接回答生成が可能かを判断してください。
    答えが曖昧な場合は、Web検索で正しい結果が必要になります。
    Web検索が必要な場合は、'はい'
    Web検索が必要ない場合は、'いいえ' を返して下さい。
    必ず 'はい' か 'いいえ' で返して下さい。それ以外は不要です。
    
    質問: {question}
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["question"],
)

# クエリ変換のプロンプト定義
query_prompt = PromptTemplate(
    template="""  
    <|begin_of_text|>
    <|start_header_id|>system<|end_header_id|>
    あなたはリサーチ質問のために最適なWeb検索クエリを作成する専門家です。
    ユーザーの質問を最も効果的な検索クエリ(検索に使用するワードリスト)に変換し、
    単語と単語の間は半角空白で区切って下さい。
    そして、記号ぬきで英語だけの検索クエリを返して下さい。それ以外は不要です。
    
    質問: {question}
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["question"],
)

# グラフの状態を定義
class GraphState(TypedDict):
    question: str
    generation: str
    search_query: str
    context: str
    action: str  # ルートするアクションを追加

# 生成
def generate(state: GraphState):
    # 必要な入力データの取得
    question = state["question"]
    context = state["context"]

    # Ollama 用にメッセージを構築
    headerstr = {"Content-Type": "application/json"}
    jsonstr = {
        "model": "yourmodel",
        "messages": [{
            "role": "user",
            "content": question,
        }]
    }

    state["generation"] = ''

    # LLM の呼び出し
    response = requests.post(API_SERVER_URL, headers=headerstr, json=jsonstr)

    # レスポンスが成功した場合
    if response.status_code == 200:

        try:
            # 複数行のJSON文字列をリストの形式に変換
            json_lines = response.text.strip().splitlines()

            # 応答を逐次的に表示
            for json_line in json_lines:

                contents = json.loads(json_line)
                if "message" in contents:
                    result = contents["message"].get("content", "") # 結果からテキストを取り出す
                    if state["generation"] is None:
                        state["generation"] = ''
                    state["generation"] += result

        except KeyError as e:
            # エラー生成
            state["generation"] = f"KeyError: Missing expected key in the response: {e}"
        except requests.exceptions.JSONDecodeError as e:
            # エラー生成
            state["generation"] = f"JSON Decode Error: {e}"
    else:
        state["generation"] = f"Error: {response.status_code}"

    return state

###################################################################################
# ユーザーの質問
# user_question = "今日の天気を知りたい"
# user_question = "明日の天気について教えて下さい"
# user_question = "あなたはわたし。わたしはあなた。つまり？"
user_question = "今年流行したドラマのメインキャラクターを知りたい"
###################################################################################

state = GraphState()

# プロンプトに質問を適用して生成
formatted_prompt = router_prompt.format(question=user_question)

state["question"] = formatted_prompt
state["context"] = ""

state = generate(state)

if state["generation"] in 'はい':
    print('Web検索が必要')

    # プロンプトに検索ワードを適用
    formatted_prompt = query_prompt.format(question=user_question)
    state["question"] = formatted_prompt
else:
    print('Web検索は不要 もしくは 検索できない')
    state["question"] = user_question

state["context"] = ""
state = generate(state)
print(state["generation"])
