# ============================================================
#  server.py  ——  Flask 后端服务（AI 接入网页的桥梁）
#  重点：展示"如何把 AI 接入网页"的最简实现
# ============================================================

from flask import Flask, request, jsonify
from flask_cors import CORS          # 允许前端跨域请求
from agent_core import chat          # 导入 AI 对话函数

app = Flask(__name__)
CORS(app)  # 开发阶段允许所有跨域，生产环境需限制域名


# ══════════════════════════════════════════════
# API 路由：前端发消息 → 后端转给 AI → 返回结果
# ══════════════════════════════════════════════
@app.route("/api/chat", methods=["POST"])
def chat_api():
    """
    接收 JSON: { "message": "用户输入的内容", "session_id": "可选的会话ID" }
    返回 JSON: { "reply": "AI 的回复" }
    """
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "请提供 message 字段"}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400
    
    # 获取 session_id,如果没有则使用默认值
    session_id = data.get("session_id", "default")

    try:
        ai_reply = chat(user_message, thread_id=session_id)  # 调用 AI,传递 session_id
        return jsonify({"reply": ai_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """健康检查接口，确认服务在线"""
    return jsonify({"status": "ok", "message": "AI 客服服务运行中"})


if __name__ == "__main__":
    # debug=True 时修改代码自动重载，生产环境设为 False
    app.run(host="0.0.0.0", port=5000, debug=True)
