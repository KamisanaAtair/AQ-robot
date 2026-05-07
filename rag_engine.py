"""
RAG 知识库管理模块
功能：文档加载、切片、向量化、存储到 Qdrant
"""

import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(
        self,
        knowledge_dir: str = "knowledge_base",
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "agent_knowledge",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        初始化知识库
        
        Args:
            knowledge_dir: 知识库文件夹路径
            qdrant_url: Qdrant 服务地址
            collection_name: 集合名称
            embedding_model: 嵌入模型名称
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(exist_ok=True)
        
        # 初始化 Qdrant 客户端
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        
        # 初始化向量存储
        from langchain_huggingface import HuggingFaceEmbeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,      # 每个片段 500 字符
            chunk_overlap=50,    # 重叠 50 字符
            length_function=len,
        )
        
        # 确保集合存在
        self._ensure_collection()
    
    def _ensure_collection(self):
        """确保 Qdrant 集合存在"""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # 获取嵌入维度
            test_embedding = self.embeddings.embed_query("test")
            vector_size = len(test_embedding)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            print(f"[KnowledgeBase] 创建集合: {self.collection_name} (维度: {vector_size})")
    
    def load_documents(self, file_paths: List[str] = None) -> int:
        """
        加载文档到知识库
        
        Args:
            file_paths: 文件路径列表，如果为 None 则加载 knowledge_base 目录下所有文件
            
        Returns:
            加载的文档数量
        """
        if file_paths is None:
            # 自动加载 knowledge_base 目录下的所有支持的文件
            file_paths = []
            for ext in ["*.txt", "*.pdf", "*.docx"]:
                file_paths.extend(self.knowledge_dir.glob(ext))
            file_paths = [str(p) for p in file_paths]
        
        if not file_paths:
            print("[KnowledgeBase] 未找到可加载的文档")
            return 0
        
        all_documents = []
        
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                print(f"[KnowledgeBase] 文件不存在: {file_path}")
                continue
            
            try:
                # 根据文件类型选择加载器
                if path.suffix.lower() == ".txt":
                    loader = TextLoader(str(path), encoding="utf-8")
                elif path.suffix.lower() == ".pdf":
                    loader = PyPDFLoader(str(path))
                elif path.suffix.lower() == ".docx":
                    loader = Docx2txtLoader(str(path))
                else:
                    print(f"[KnowledgeBase] 不支持的文件类型: {path.suffix}")
                    continue
                
                documents = loader.load()
                
                # 添加元数据
                for doc in documents:
                    doc.metadata["source"] = str(path)
                    doc.metadata["filename"] = path.name
                
                all_documents.extend(documents)
                print(f"[KnowledgeBase] 已加载: {path.name} ({len(documents)} 个片段)")
                
            except Exception as e:
                print(f"[KnowledgeBase] 加载失败 {path.name}: {e}")
        
        if not all_documents:
            print("[KnowledgeBase] 没有成功加载任何文档")
            return 0
        
        # 文本分割
        chunks = self.text_splitter.split_documents(all_documents)
        print(f"[KnowledgeBase] 分割为 {len(chunks)} 个文本块")
        
        # 添加到向量数据库
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        vector_store.add_documents(chunks)
        
        print(f"[KnowledgeBase] ✓ 成功索引 {len(chunks)} 个文本块")
        return len(chunks)
    
    def search(self, query: str, k: int = 3) -> List[str]:
        """
        搜索相关知识
        
        Args:
            query: 查询文本
            k: 返回最相关的 k 个结果
            
        Returns:
            相关文档片段列表
        """
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        
        docs = vector_store.similarity_search(query, k=k)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "filename": doc.metadata.get("filename", "unknown"),
            })
        
        return results
    
    def clear(self):
        """清空知识库"""
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection()
            print("[KnowledgeBase] 知识库已清空")
        except Exception as e:
            print(f"[KnowledgeBase] 清空失败: {e}")
    
    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
            }
        except Exception as e:
            return {"error": str(e)}
