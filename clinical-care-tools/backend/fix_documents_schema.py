import asyncio
from app.db.session import engine
from sqlalchemy import text

async def fix():
    # Use sync engine URL for direct connect? Or async engine?
    # engine is async.
    async with engine.begin() as conn:
        print("Adding columns logic...")
        cols = [
            ("processing_status", "VARCHAR(20) DEFAULT 'PENDING' NOT NULL"),
            ("content_type", "VARCHAR(100) DEFAULT 'application/octet-stream' NOT NULL"),
            ("file_size", "INTEGER DEFAULT 0 NOT NULL"),
            ("project_id", "UUID REFERENCES projects(id) ON DELETE CASCADE"),
            ("uploaded_by", "UUID REFERENCES users(id)"),
            ("filename", "VARCHAR(255) DEFAULT 'legacy' NOT NULL"),
            ("content_hash", "VARCHAR(64) DEFAULT 'legacy_hash' NOT NULL"),
            ("encrypted_content", "BYTEA DEFAULT ''::bytea NOT NULL"),
            ("encryption_algorithm", "VARCHAR(50) DEFAULT 'AES-256-GCM' NOT NULL")
        ]
        
        for name, defn in cols:
            try:
                # Note: IF NOT EXISTS is valid in Postgres 9.6+
                await conn.execute(text(f"ALTER TABLE documents ADD COLUMN IF NOT EXISTS {name} {defn}"))
                print(f"Ensured {name}")
            except Exception as e:
                print(f"Error adding {name}: {e}")

if __name__ == "__main__":
    asyncio.run(fix())
