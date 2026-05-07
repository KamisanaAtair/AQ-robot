# AI 客服 Agent - RAG 增强版

基于 LangChain v1 + Qdrant 向量数据库的 RAG（检索增强生成）智能客服系统。

## ✨ 特性

- 🤖 **智能对话**：基于通义千问的自然语言理解
- 🔍 **RAG 检索**：从本地知识库精准检索相关信息
- 🌐 **网络搜索**：集成百度搜索获取实时信息
- 💾 **向量数据库**：Qdrant 高效存储和检索
- 📚 **多格式支持**：支持 TXT、PDF、DOCX 文档
- 🧠 **对话记忆**：自动维护多轮对话上下文
- ⚡ **快速部署**：uv 包管理，一键启动

## 📁 项目结构

```
Agenttest/
├── knowledge_base/          # 本地知识库文件夹
│   └── *.txt/pdf/docx      # 放入你的文档
├── rag_engine.py           # RAG 核心引擎（文档加载、向量化、存储）
├── rag_agent.py            # RAG Agent（整合检索和对话）
├── manage_kb.py            # 知识库管理工具
├── agent_core.py           # 基础客服 Agent（无 RAG）
├── server.py               # Flask API 服务
├── index.html              # 前端页面
├── pyproject.toml          # uv 依赖配置
├── uv.lock                 # 依赖锁定文件
└── RAG_GUIDE.md            # RAG 详细使用指南
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd D:\Project\Agenttest
uv sync
```

### 2. 启动 Qdrant 向量数据库

**方式一：Docker（推荐）**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**方式二：本地安装**
访问 https://qdrant.tech/documentation/quick-start/ 下载安装

### 3. 配置 API Key

编辑 `rag_agent.py`，替换：
- `YOUR_DASHSCOPE_API_KEY` → 阿里云百炼平台 API Key
- `YOUR_BAIDU_KEY` → 百度搜索 API Key

**获取地址：**
- 阿里云：https://bailian.console.aliyun.com/
- 百度：https://console.bce.baidu.com/qianfan/tools/toolsCenter/web_search/detail

### 4. 准备知识库文档

将文档放入 `knowledge_base` 文件夹：
```
knowledge_base/
├── 产品手册.txt
├── 常见问题.pdf
└── 公司政策.docx
```

### 5. 加载文档到知识库

```bash
uv run python manage_kb.py
```

在交互界面输入：
```
> load
```

系统会自动加载所有文档并进行：
- 文档解析
- 文本分割（500字符/段）
- 向量化（sentence-transformers）
- 存储到 Qdrant

### 6. 启动 RAG Agent

**命令行模式：**
```bash
uv run python rag_agent.py
```

**Web 服务模式：**
修改 `server.py` 第 8 行：
```python
from rag_agent import chat  # 改为使用 RAG Agent
```

然后运行：
```bash
uv run python server.py
```

用浏览器打开 `index.html` 即可使用。

## 🛠️ 知识库管理

运行 `uv run python manage_kb.py` 后可用命令：

| 命令 | 说明 | 示例 |
|------|------|------|
| `load` | 加载所有文档 | `> load` |
| `search <查询>` | 测试搜索 | `> search 产品价格` |
| `stats` | 查看统计 | `> stats` |
| `clear` | 清空知识库 | `> clear` |
| `quit` | 退出 | `> quit` |

## 🔄 工作流程

```
用户问题 
  ↓
Agent (rag_agent.py)
  ↓
决策：需要检索吗？
  ↓
rag_search 工具
  ↓
Qdrant 向量数据库 ← HuggingFace Embeddings
  ↓
Top-K 相关文档片段
  ↓
LLM 综合信息生成回答
```


## 📊 技术栈

- **框架**：LangChain v1 + LangGraph
- **向量数据库**：Qdrant
- **嵌入模型**：sentence-transformers/all-MiniLM-L6-v2
- **LLM**：阿里云通义千问 (qwen-turbo)
- **后端**：Flask 3.0
- **包管理**：uv
- **前端**：原生 HTML/CSS/JS

## 📝 其他模块

### 基础客服 Agent (agent_core.py)

不包含 RAG 功能的简化版 Agent，仅支持百度搜索。适合快速测试或不需要知识库的场景。

```bash
uv run python agent_core.py
```

### Web 服务 (server.py)

提供 RESTful API 接口：

**POST /api/chat**
```json
// 请求
{
  "message": "你好",
  "session_id": "user_123"  // 可选
}

// 响应
{
  "reply": "你好！有什么可以帮助你的？"
}
```

**GET /api/health**
```json
{
  "status": "ok",
  "message": "AI 客服服务运行中"
}
```

## ⚙️ 配置说明

### 修改嵌入模型

编辑 `rag_engine.py`：
```python
kb = KnowledgeBase(
    embedding_model="BAAI/bge-base-zh-v1.5",  # 更好的中文支持
)
```

推荐的中文模型：
- `BAAI/bge-small-zh-v1.5`（快速）
- `BAAI/bge-base-zh-v1.5`（平衡）
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`（多语言）

### 调整文本分割参数

编辑 `rag_engine.py`：
```python
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # 增大片段长度
    chunk_overlap=100,    # 增大重叠
)
```
## 一些问题
- 嵌入模型：使用的模型是英语语料库训练出来的，面对汉语语境的时候可能表现不佳
- 文本库：可以使用mysql等DBSM，但是这里为了方便就用ai弄了个简单数据库类