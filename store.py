import threading
from typing import List, Dict, Optional
from database.db import get_connection


class MemoryStore:
    """Enhanced persistent memory storage using MySQL"""

    def __init__(self):
        self.lock = threading.Lock()

    # =========================
    # INSERT MEMORY
    # =========================
    def insert(self, memory: Dict, user_id: str) -> bool:
        with self.lock:
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)

                similar = self._find_similar_memories(
                    memory["content"], memory["type"], user_id
                )

                if similar:
                    existing_id = similar[0]['id']
                    existing_confidence = similar[0]['confidence']

                    new_confidence = min(
                        0.99,
                        (existing_confidence + memory["confidence"]) / 2 + 0.05
                    )

                    self.update_confidence(existing_id, new_confidence)
                    self.update_last_used(existing_id, memory["created_turn"])

                    self._log_history(existing_id, "reinforced",
                                      existing_confidence, new_confidence)
                    conn.close()
                    return True

                self._deactivate_conflicts(
                    memory["type"], memory["content"], user_id
                )

                cursor.execute("""
                INSERT INTO memory 
                (id, user_id, type, content, confidence, 
                 created_turn, last_used_turn, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    memory["id"],
                    user_id,
                    memory["type"],
                    memory["content"],
                    memory["confidence"],
                    memory["created_turn"],
                    memory["last_used_turn"],
                    memory["active"]
                ))

                self._log_history(memory["id"], "created",
                                  None, memory["confidence"])

                conn.commit()
                conn.close()
                return True

            except Exception as e:
                print("Insert error:", e)
                return False

    # =========================
    # FIND SIMILAR
    # =========================
    def _find_similar_memories(self, content, mem_type, user_id,
                               threshold=0.7):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT id, content, confidence, created_turn, last_used_turn
        FROM memory
        WHERE user_id = %s AND type = %s AND active = 1
        """, (user_id, mem_type))

        memories = cursor.fetchall()
        conn.close()

        similar = []
        content_words = set(content.lower().split())

        for mem in memories:
            mem_words = set(mem['content'].lower().split())

            if not content_words or not mem_words:
                continue

            intersection = len(content_words & mem_words)
            union = len(content_words | mem_words)

            if union > 0:
                similarity = intersection / union
                if similarity >= threshold:
                    similar.append(mem)

        return similar

    # =========================
    # LOG HISTORY
    # =========================
    def _log_history(self, memory_id, action,
                     old_confidence, new_confidence):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO memory_history
        (memory_id, action, old_confidence, new_confidence)
        VALUES (%s, %s, %s, %s)
        """, (memory_id, action, old_confidence, new_confidence))

        conn.commit()
        conn.close()

    # =========================
    # UPDATE LAST USED
    # =========================
    def update_last_used(self, mem_id, turn):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE memory
        SET last_used_turn = %s,
            use_count = use_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """, (turn, mem_id))

        conn.commit()
        conn.close()

    # =========================
    # UPDATE CONFIDENCE
    # =========================
    def update_confidence(self, mem_id, new_confidence):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE memory
        SET confidence = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """, (new_confidence, mem_id))

        conn.commit()
        conn.close()

    # =========================
    # FETCH ACTIVE
    # =========================
    def fetch_active(self, user_id, limit=None):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, type, content, confidence, 
               created_turn, last_used_turn, use_count
        FROM memory
        WHERE user_id = %s AND active = 1
        ORDER BY confidence DESC, last_used_turn DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        conn.close()

        return results
