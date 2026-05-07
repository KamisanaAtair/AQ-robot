"""
知识库管理脚本
用于加载、管理本地知识库文档
"""

from rag_engine import KnowledgeBase


def main():
    """交互式知识库管理"""
    
    kb = KnowledgeBase(
        knowledge_dir="knowledge_base",
        qdrant_url="http://localhost:6333",
        collection_name="agent_knowledge",
    )
    
    print("=" * 60)
    print("知识库管理系统")
    print("=" * 60)
    print("\n可用命令:")
    print("  load          - 加载 knowledge_base 目录下的所有文档")
    print("  search <查询>  - 搜索相关知识")
    print("  stats         - 查看知识库统计信息")
    print("  clear         - 清空知识库")
    print("  quit          - 退出\n")
    
    while True:
        try:
            command = input("> ").strip()
            
            if not command:
                continue
            
            parts = command.split(maxsplit=1)
            cmd = parts[0].lower()
            
            if cmd == "quit":
                break
            
            elif cmd == "load":
                print("\n正在加载文档...")
                count = kb.load_documents()
                print(f"\n✓ 完成！共加载 {count} 个文本块\n")
            
            elif cmd == "search":
                if len(parts) < 2:
                    print("用法: search <查询关键词>\n")
                    continue
                
                query = parts[1]
                print(f"\n搜索: {query}\n")
                results = kb.search(query, k=3)
                
                if not results:
                    print("未找到相关结果\n")
                else:
                    for i, result in enumerate(results, 1):
                        print(f"[{i}] {result['content']}")
                        print(f"    来源: {result['filename']}\n")
            
            elif cmd == "stats":
                stats = kb.get_stats()
                print("\n知识库统计:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                print()
            
            elif cmd == "clear":
                confirm = input("确认清空知识库？(yes/no): ").strip().lower()
                if confirm == "yes":
                    kb.clear()
                    print()
                else:
                    print("已取消\n")
            
            else:
                print(f"未知命令: {cmd}\n")
        
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"错误: {e}\n")
    
    print("再见！")


if __name__ == "__main__":
    main()
