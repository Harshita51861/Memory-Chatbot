# backend/app.py

"""
Memory Chatbot Backend - MySQL Version
Logic unchanged. SQLite fully removed.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from datetime import datetime
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Import configurations
from config import Config

# Import memory modules
from long_term.contract import is_valid_memory
from long_term.extractor import extract_memory, extract_name, extract_multiple
from long_term.store import MemoryStore
from long_term.decay import apply_smart_decay, refresh_memory, get_decay_stats, boost_related_memories
from long_term.retrieval import (
    retrieve_relevant, retrieve_by_type, get_user_name,
    get_user_preferences, get_commitments, search_memories
)
from long_term.injector import (
    inject_memory_context, get_memory_summary,
    create_memory_card, format_memories_for_display
)

# Import LLM
from llm.simple_llm import SimpleLLM

# Import auth (fallback if missing)
try:
    from auth.admin_auth import AdminAuth
except ImportError:
    class AdminAuth:
        def __init__(self, username, password):
            self.username = username
            self.password = password

        def verify_credentials(self, username, password):
            return username == self.username and password == self.password

        def require_auth(self, f):
            return f


# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize components
memory_store = MemoryStore()   # ✅ FIXED (Removed DATABASE_PATH)
llm = SimpleLLM()
admin_auth = AdminAuth(Config.ADMIN_USERNAME, Config.ADMIN_PASSWORD)

# Session tracking
user_sessions = {}


def get_or_create_session(user_id: str = "default"):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "turn": 1,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }
    else:
        user_sessions[user_id]["last_active"] = datetime.now().isoformat()

    return user_sessions[user_id]


def log_error(error: Exception, context: str = ""):
    print("\n" + "=" * 60)
    print(f"ERROR in {context}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Error: {str(error)}")
    traceback.print_exc()
    print("=" * 60 + "\n")


# ================= PUBLIC API =================

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        stats = memory_store.get_stats("default")
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "memory_stats": stats,
            "active_sessions": len(user_sessions)
        })
    except Exception as e:
        log_error(e, "health_check")
        return jsonify({"status": "degraded", "error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '').strip()
        user_id = data.get('user_id', 'default')

        if not message:
            return jsonify({"error": "Message is required"}), 400

        session = get_or_create_session(user_id)
        current_turn = session["turn"]

        new_memories = extract_multiple(message, current_turn, user_id)
        memories_created = []

        for new_memory in new_memories:
            if memory_store.insert(new_memory, user_id):
                memories_created.append(new_memory)

        primary_memory = memories_created[0] if memories_created else None

        apply_smart_decay(memory_store, user_id, current_turn)

        active_memories = memory_store.fetch_active(user_id)
        relevant_memories = retrieve_relevant(
            message, active_memories, top_k=5, min_score=0.1
        )

        query_words = message.lower().split()
        boost_related_memories(
            memory_store, user_id, current_turn, query_words, boost_amount=0.01
        )

        for mem in relevant_memories:
            refresh_memory(memory_store, mem["id"], current_turn, boost=0.01)

        memory_context = inject_memory_context(relevant_memories, style="detailed")
        user_name = get_user_name(active_memories)

        response_text = llm.generate_response(
            message,
            memory_context,
            primary_memory,
            user_name
        )

        summary = get_memory_summary(relevant_memories)
        session["turn"] += 1

        return jsonify({
            "response": response_text,
            "turn": current_turn,
            "memory_used": len(relevant_memories) > 0,
            "new_memories_created": len(memories_created),
            "memories_created": memories_created,
            "relevant_memories": relevant_memories,
            "memory_summary": summary,
            "user_name": user_name
        })

    except Exception as e:
        log_error(e, "chat")
        return jsonify({
            "error": "An error occurred processing your message",
            "details": str(e) if app.debug else None
        }), 500


# ================= MAIN =================

if __name__ == '__main__':
    print("🧠 Memory Chatbot Backend Starting...")
    print(f"🗄️ MySQL Database: {Config.MYSQL_DATABASE}")  # ✅ FIXED
    print(f"🔐 Admin: {Config.ADMIN_USERNAME}")
    print(f"🌐 CORS Origins: {Config.CORS_ORIGINS}")
    print("🚀 Server running on http://localhost:5000\n")

    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
