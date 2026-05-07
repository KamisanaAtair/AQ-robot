import os
import requests                                                 # 百度搜索需要
from langchain_community.chat_models import ChatTongyi          # 千问模型
from langchain_core.messages import HumanMessage                # 消息类型
from langchain.tools import tool                                # 工具装饰器
from langchain.agents import create_agent                       # v1 Agent 创建器
from langgraph.checkpoint.memory import InMemorySaver           # 内存型会话保存

os.environ["DASHSCOPE_API_KEY"]     = "YOUR_DASHSCOPE_API_KEY"   # 千问
os.environ["BAIDU_API_KEY"]         = "bce-v3/ALTAK-5HQ1Q8UgLi7ZiDS3zEFcV/674fc13625b67fe8c45e6286af4b5d451eda82f5"       # 百度搜索 API Key

llm = ChatTongyi(
    model="qwen-turbo",   # 可换 qwen-plus / qwen-max
    temperature=0.7,
)

SYSTEM_PROMPT = """你是一名专业、友好的 AI 客服助手。
你可以：
- 回答用户关于产品、服务的问题
- 使用搜索工具查询最新信息
- 记住本次对话的上下文

请用简洁、礼貌的中文回复用户。
如果不确定，请使用搜索工具获取最新信息，不要编造答案。"""


@tool
def baidu_search(query: str) -> str:
    """
    当需要查询实时信息、新闻、或你不确定的事实时使用此工具。输入搜索关键词。
    """
    api_key = os.getenv("BAIDU_API_KEY")
    if not api_key or api_key == "YOUR_BAIDU_API_KEY":
        return "百度搜索 API 未配置，请设置 BAIDU_API_KEY"
    
    try:
        # 百度搜索 API 端点（根据百度千帆平台文档）
        url = f"https://aip.baidubce.com/rest/2.0/ai_platform/v1/tools/web_search?access_token={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "count": 3  # 返回 3 条结果
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        
        # 格式化搜索结果
        formatted_results = []
        for item in results.get("result", [])[:3]:
            title = item.get("title", "")
            link = item.get("link", "")
            abstract = item.get("abstract", "")
            formatted_results.append(f"标题：{title}\n链接：{link}\n摘要：{abstract}\n")
        
        return "\n".join(formatted_results) if formatted_results else "未找到相关结果"
        
    except Exception as e:
        return f"百度搜索失败:{str(e)}"


checkpointer = InMemorySaver()  # 内存型会话状态保存

# 创建 Agent+ReAct 策略
agent = create_agent(
    model=llm,
    tools=[baidu_search],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)


# 对网页端接口
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
    # 从返回的消息列表中获取最后一条 AI 消息的内容
    return result["messages"][-1].content


# 测试入口
if __name__ == "__main__":
    print("=== 客服 AI 启动（输入 quit 退出）===")
    while True:
        user = input("\n你: ").strip()
        if user.lower() == "quit":
            break
        reply = chat(user)
        print(f"AI: {reply}")
