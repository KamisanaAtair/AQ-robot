# RAG 知识库使用指南

## 架构说明

本项目实现了完整的 RAG (Retrieval-Augmented Generation) 系统：

```
用户问题 → Agent → rag_search 工具 → Qdrant 向量数据库 → 相关知识 → LLM 生成回答
```

## 文件结构

```
Agenttest/
├── knowledge_base/          # 本地知识库文件夹
│   ├── *.txt               # 支持 txt 格式
│   ├── *.pdf               # 支持 pdf 格式
│   └── *.docx              # 支持 docx 格式
├── rag_engine.py           # RAG 核心引擎（文档加载、向量化、存储）
├── rag_agent.py            # RAG Agent（整合搜索和对话）
├── manage_kb.py            # 知识库管理工具
├── agent_core.py           # 原客服 Agent（无 RAG）
└── server.py               # Flask API 服务
```

## 快速开始

### 1. 启动 Qdrant 向量数据库

**方式一：Docker（推荐）**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**方式二：本地安装**
访问 https://qdrant.tech/documentation/quick-start/ 下载安装

### 2. 准备知识库文档

将你的文档放入 `knowledge_base` 文件夹：
- `.txt` 文本文件
- `.pdf` PDF 文档
- `.docx` Word 文档

示例：
```
knowledge_base/
├── 产品手册.txt
├── 常见问题.pdf
└── 公司政策.docx
```

### 3. 加载文档到知识库

```bash
uv run python manage_kb.py
```

在交互界面输入：
```
> load
```

系统会自动加载 `knowledge_base` 目录下的所有文档，并进行：
- 文档解析
- 文本分割（每段 500 字符，重叠 50 字符）
- 向量化（使用 sentence-transformers）
- 存储到 Qdrant

### 4. 启动 RAG Agent

```bash
uv run python rag_agent.py
```

现在可以对话了！Agent 会：
1. 优先使用 `rag_search` 查询本地知识库
2. 如果没有相关信息，使用 `baidu_search` 查询网络
3. 综合信息后生成回答

### 5. （可选）启动 Web 服务

修改 `server.py` 导入 `rag_agent`：

```python
from rag_agent import chat  # 改为使用 RAG Agent
```

然后运行：
```bash
uv run python server.py
```

## 知识库管理命令

运行 `uv run python manage_kb.py` 后可用命令：

| 命令 | 说明 | 示例 |
|------|------|------|
| `load` | 加载所有文档 | `> load` |
| `search` | 测试搜索 | `> search 产品价格` |
| `stats` | 查看统计 | `> stats` |
| `clear` | 清空知识库 | `> clear` |
| `quit` | 退出 | `> quit` |

## 配置说明

### 修改嵌入模型

编辑 `rag_engine.py`：

```python
kb = KnowledgeBase(
    embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 支持中文
)
```

推荐的中文模型：
- `BAAI/bge-small-zh-v1.5`
- `BAAI/bge-base-zh-v1.5`
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

### 修改文本分割参数

编辑 `rag_engine.py`：

```python
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # 增大片段长度
    chunk_overlap=100,    # 增大重叠
)
```

### 修改 Qdrant 地址

如果使用远程 Qdrant：

```python
kb = KnowledgeBase(
    qdrant_url="https://your-qdrant-server:6333",
)
```

## 工作流程

1. **用户提问**："公司的休假政策是什么？"

2. **Agent 决策**：调用 `rag_search("公司的休假政策")`

3. **RAG 检索**：
   - 将问题向量化
   - 在 Qdrant 中搜索最相似的文档片段
   - 返回 Top 3 相关结果

4. **生成回答**：
   ```
   根据知识库中的信息：
   [1] 公司员工每年享有 15 天带薪年假...
   
   公司的休假政策是：员工每年享有 15 天带薪年假。
   ```

## 技术栈

- **向量数据库**: Qdrant
- **嵌入模型**: sentence-transformers (HuggingFace)
- **文本分割**: LangChain RecursiveCharacterTextSplitter
- **文档加载**: TextLoader, PyPDFLoader, Docx2txtLoader
- **相似度搜索**: Cosine Similarity

## 注意事项

1. **首次运行较慢**：需要下载嵌入模型（约 500MB）
2. **Qdrant 必须运行**：否则无法存储和检索向量
3. **文档格式**：确保文档编码为 UTF-8
4. **中文支持**：默认模型对中文支持一般，建议更换为专门的中文模型

## 故障排查

### Qdrant 连接失败
```bash
# 检查 Qdrant 是否运行
curl http://localhost:6333/collections

# 启动 Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### 文档加载失败
- 检查文件格式是否正确
- 检查文件编码（应为 UTF-8）
- 查看详细错误信息

### 搜索结果为空
- 确认已执行 `load` 命令
- 检查查询关键词是否与文档内容相关
- 使用 `stats` 查看是否有数据
