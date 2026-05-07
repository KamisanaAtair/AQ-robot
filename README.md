# AI 客服 Agent —— 学习项目

## 项目结构
```
Agenttest/
├── agent_core.py   # ★ 核心：LangChain Agent（重点学习文件）
├── server.py       # Flask 后端（AI 接入网页的桥梁）
├── index.html      # 前端页面（纯 HTML，无需框架）
└── requirements.txt
```

## 核心概念对应关系

| 概念 | 代码位置 | 说明 |
|------|---------|------|
| **创建实例** | `agent_core.py` 第①步 | `ChatTongyi(...)` 创建千问模型 |
| **提示工程** | `agent_core.py` 第②步 | `ChatPromptTemplate` 定义系统角色 |
| **工具 (Tool)** | `agent_core.py` 第③步 | 封装百度搜索 |
| **记忆** | `agent_core.py` 第④步 | `ConversationBufferMemory` 保存历史 |
| **Agent+ReAct** | `agent_core.py` 第⑤步 | `create_react_agent` + `AgentExecutor` |
| **接入网页** | `server.py` + `index.html` | Flask API ↔ fetch 请求 |

## 快速启动

### 1. 安装依赖
```bash
cd D:\Project\Agenttest
pip install -r requirements.txt
```

### 2. 填写 API Key
打开 `agent_core.py`，替换：
- `YOUR_DASHSCOPE_API_KEY` → 阿里云百炼平台的 API Key
- `YOUR_BAIDU_API_KEY` → 百度智能云千帆平台的 API Key

### 3. 启动后端
```bash
python server.py
# 看到 "Running on http://0.0.0.0:5000" 即成功
```

### 4. 打开前端
直接用浏览器打开 `index.html` 文件即可。

---

## 网页接入原理（重点）

```
用户在 index.html 输入消息
        ↓  fetch POST /api/chat
   server.py (Flask)
        ↓  调用 chat()
   agent_core.py (LangChain Agent)
        ↓  需要时调用工具
   Baidu Search API
        ↓  返回结果
   AI 生成回复 → Flask → 前端显示
```

**关键代码只有两处：**

后端（server.py）：
```python
@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.get_json()
    reply = chat(data["message"])          # 调用 AI
    return jsonify({"reply": reply})
```

前端（index.html）：
```javascript
const response = await fetch("http://localhost:5000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),   // 发给后端
});
const data = await response.json();           // 接收回复
```

这就是 **"前后端分离"** 的最简模型：前端只负责显示，后端只负责 AI 逻辑，通过 HTTP JSON 通信。

## API Key 获取地址

### 阿里云千问 API Key
访问：https://bailian.console.aliyun.com/
1. 登录阿里云账号
2. 进入百炼控制台
3. 在 API Key 管理页面创建或获取 API Key

### 百度搜索 API Key
访问：https://console.bce.baidu.com/qianfan/tools/toolsCenter/web_search/detail
1. 登录百度智能云账号
2. 进入千帆大模型平台
3. 在工具中心找到 Web 搜索工具
4. 创建应用并获取 API Key
5. 注意：可能需要实名认证才能使用百度搜索服务

## 常见问题

### Q1: 没有百度 API Key 可以运行吗？
可以的！代码中已经做了处理，如果 API Key 未配置，搜索工具会返回提示信息，AI 仍然可以正常对话，只是无法使用搜索功能。

### Q2: 为什么选择百度搜索而不是 Google？
- 百度搜索在国内访问更稳定
- 百度千帆平台提供完善的 API 支持
- 更适合中文用户的学习和使用
