"""
RAG Agent 核心
整合 RAG 检索和对话能力
"""

import os
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from rag_engine import KnowledgeBase


# API 密钥
os.environ["DASHSCOPE_API_KEY"] = "YOUR_DASHSCOPE_API_KEY"
os.environ["BAIDU_API_KEY"] = "YOUR_BAIDU_KEY"


# 初始化知识库
kb = KnowledgeBase(
    knowledge_dir="knowledge_base",
    qdrant_url="http://localhost:6333",
    collection_name="agent_knowledge",
)


# RAG 搜索工具
@tool
def rag_search(query: str) -> str:
    """
    从本地知识库中搜索相关信息。当用户询问公司内部知识、产品文档、政策规定等时使用此工具。
    输入：搜索关键词或问题
    返回：相关知识片段
    """
    results = kb.search(query, k=3)
    
    if not results:
        return "未在知识库中找到相关信息"
    
    formatted_results = []
    for i, result in enumerate(results, 1):
        formatted_results.append(
            f"[{i}] {result['content']}\n   来源: {result['filename']}"
        )
    
    return "\n\n".join(formatted_results)


# 百度搜索工具（保留原有功能）
@tool
def baidu_search(query: str) -> str:
    """
    当需要查询实时信息、新闻、或你不确定的事实时使用此工具。输入搜索关键词。
    """
    import requests
    
    api_key = os.getenv("BAIDU_API_KEY")
    if not api_key or api_key == "YOUR_BAIDU_KEY":
        return "百度搜索 API 未配置，请设置 BAIDU_API_KEY"
    
    try:
        url = f"https://aip.baidubce.com/rest/2.0/ai_platform/v1/tools/web_search?access_token={api_key}"
        
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "query": query,
            "count": 3
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        
        formatted_results = []
        for item in results.get("result", [])[:3]:
            title = item.get("title", "")
            link = item.get("link", "")
            abstract = item.get("abstract", "")
            formatted_results.append(f"标题：{title}\n链接：{link}\n摘要：{abstract}\n")
        
        return "\n".join(formatted_results) if formatted_results else "未找到相关结果"
        
    except Exception as e:
        return f"百度搜索失败:{str(e)}"


# 系统提示词
SYSTEM_PROMPT = """你是一名专业、友好的 AI 客服助手。

你可以：
- 回答用户关于产品、服务的问题
- 使用 rag_search 工具查询本地知识库中的内部信息
- 使用 baidu_search 工具查询最新的公开信息
- 记住本次对话的上下文

请用简洁、礼貌的中文回复用户。
如果不确定，请使用搜索工具获取最新信息，不要编造答案。

优先使用 rag_search 查询内部知识，如果没有相关信息再使用 baidu_search。"""


# 初始化 LLM
llm = ChatTongyi(
    model="qwen-turbo",
    temperature=0.7,
)


# 记忆系统
checkpointer = InMemorySaver()


# 创建 Agent
agent = create_agent(
    model=llm,
    tools=[rag_search, baidu_search],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)


def chat(user_input: str, thread_id: str = "default") -> str:
    """
    接收用户消息,返回 AI 回复字符串。
    内部自动维护对话记忆(通过 thread_id 区分不同会话)。
    
    参数:
        user_input: 用户输入的消息
        thread_id: 会话 ID,用于区分不同用户的对话历史
    """
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config
    )
    return result["messages"][-1].content


if __name__ == "__main__":
    print("=== RAG 客服 AI 启动（输入 quit 退出）===")
    print("提示: 请先在 knowledge_base 文件夹中放入文档 (.txt/.pdf/.docx)")
    print("然后运行 kb.load_documents() 加载文档\n")
    
    while True:
        user = input("\n你: ").strip()
        if user.lower() == "quit":
            break
        reply = chat(user)
        print(f"AI: {reply}")
