"""
Manual database schema fix script.
Creates projects table and updates documents table with required columns.
"""
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def fix_schema():
    async with engine.begin() as conn:
        print("Dropping existing tables if any...")
        await conn.execute(text("DROP TABLE IF EXISTS project_members CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS projects CASCADE"))
        
        print("Creating projects table...")
        await conn.execute(text("""
            CREATE TABLE projects (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                description TEXT,
                created_by UUID NOT NULL REFERENCES users(id),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
            )
        """))
        await conn.execute(text("CREATE INDEX ix_projects_name ON projects(name)"))
        
        print("Creating project_members table...")
        await conn.execute(text("""
            CREATE TABLE project_members (
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                added_by UUID REFERENCES users(id) NOT NULL,
                added_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
                PRIMARY KEY (project_id, user_id)
            )
        """))
        
        print("Updating documents table...")
        # Add columns with IF NOT EXISTS (PostgreSQL 9.6+)
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS filename VARCHAR(255) DEFAULT 'legacy' NOT NULL"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64) DEFAULT 'legacy_hash' NOT NULL"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS encrypted_content BYTEA DEFAULT ''::bytea NOT NULL"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS encryption_algorithm VARCHAR(50) DEFAULT 'AES-256-GCM' NOT NULL"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0 NOT NULL"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'PENDING' NOT NULL"))
        await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(100) DEFAULT 'application/octet-stream' NOT NULL"))
        
        # uploaded_by needs a valid user default - get admin user
        result = await conn.execute(text("SELECT id FROM users WHERE username = 'admin' LIMIT 1"))
        user_row = result.first()
        if user_row:
            user_id = str(user_row[0])
            await conn.execute(text(f"ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_by UUID DEFAULT '{user_id}'::uuid REFERENCES users(id)"))
        else:
            print("Warning: No admin user found, uploaded_by column may need manual default")
            await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES users(id)"))
        
        print("Schema fix complete!")

if __name__ == "__main__":
    asyncio.run(fix_schema())
