from database.db import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Memory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id VARCHAR(255) PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        type VARCHAR(100) NOT NULL,
        content TEXT NOT NULL,
        confidence FLOAT NOT NULL,
        created_turn INT NOT NULL,
        last_used_turn INT NOT NULL,
        use_count INT DEFAULT 1,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        metadata TEXT
    )
    """)

    cursor.execute("""
    CREATE INDEX idx_user_active ON memory(user_id, active)
    """)

    cursor.execute("""
    CREATE INDEX idx_type ON memory(type)
    """)

    cursor.execute("""
    CREATE INDEX idx_confidence ON memory(confidence)
    """)

    cursor.execute("""
    CREATE INDEX idx_last_used ON memory(last_used_turn)
    """)

    # Memory History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        memory_id VARCHAR(255) NOT NULL,
        action VARCHAR(100) NOT NULL,
        old_confidence FLOAT,
        new_confidence FLOAT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (memory_id) REFERENCES memory(id)
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ MySQL Tables Created Successfully")

if __name__ == "__main__":
    init_db()
