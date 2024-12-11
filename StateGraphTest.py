from langchain.prompts import PromptTemplate
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict
import streamlit as st

# グラフの状態を定義
class GraphState(TypedDict):
    question: str
    generation: str
    context: str
    action: str  # ルートするアクションを追加

# ユーザーの質問をWeb検索用のクエリに変換する関数
def transform_query(state: GraphState):
    return state

# Web検索結果や質問に基づいて回答を生成する関数
# グラフ状態の生成部分の修正
def generate(state: GraphState):
    # 必要な入力データの取得
    question = state["question"]
    context = state["context"]
    if state["action"] == "transform_query":        # web
        state["generation"] = "web検索した結果を表示中"
    else:                                           # llm
        state["generation"] = "llmの生成した結果を表示中"
    return state

# 質問に基づいて、Web検索を実行すべきか、直接生成すべきかを判断する関数
def route_question(state: GraphState):
    if "?" in state["question"]:  # 質問に「？」が含まれていればWeb検索を推奨
        state["action"] = "transform_query"
    else:
        state["action"] = "generate"
    return state

#条件付きエッジの実装
def should_search(state: GraphState):
    if "transform_query" == state["action"]:
        return "web"
    else:
        return "llm"


# ユーザーの質問を元にWeb検索を実行し、その結果を state に保存する関数
def web_search(state: GraphState):
    return state

# ワークフローの定義
workflow = StateGraph(GraphState)

# ノードを追加
workflow.add_node("route_question", route_question)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)
workflow.add_node("web_search", web_search)

# ノード間の遷移を設定
# route_question → transform_query
# route_question → generate        という条件付きエッジを作成
workflow.add_conditional_edges(
    #開始ノードを指定
    "route_question",
    #条件が定義されどのノードを呼ぶか判断する関数を指定
    should_search,
    {
        # 変換(web検索)
        "web": "transform_query",
        # 生成
        "llm": "generate"
    }
)
workflow.add_edge("transform_query", "web_search")          # 変換から検索
workflow.add_edge("web_search", "generate")                 # 検索から生成
workflow.add_edge("generate", END)                          # 変換から終了

# 初期ノードを設定
workflow.set_entry_point("route_question")

# コンパイルしてエージェントを作成
local_agent = workflow.compile()

# エージェントを実行する関数
def run_agent(query):
    output = local_agent.invoke({"question": query})
    return output["generation"]

# Streamlit UI
st.title("StateGraph の動作確認")
st.text("入力に「?」があると web_search")
st.text("入力に「?」がないと generate")

user_query = st.text_input("調査文字列を入力して下さい:", "")

if st.button("クエリを実行"):
    if user_query:
        st.write(run_agent(user_query))
