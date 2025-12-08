import asyncio
import sys
import uuid
import bcrypt
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def create_user():
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(text("SELECT id FROM users WHERE username = 'admin'"))
        user = result.scalar_one_or_none()
        
        # Hash password
        password = "StrongAdminPass1!"
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

        if user:
            print("User 'admin' already exists. Updating password...")
            await session.execute(text("UPDATE users SET password_hash = :hash WHERE username = 'admin'"), {"hash": hashed})
            await session.commit()
            print("Password updated.")
            return

        print("Creating user 'admin'...")
        
        # Insert raw SQL
        user_id = uuid.uuid4()
        query = text("""
            INSERT INTO users (id, username, email, password_hash, role, is_active, can_break_glass, created_at, updated_at)
            VALUES (:id, :username, :email, :password_hash, :role, :is_active, :can_break_glass, NOW(), NOW())
        """)
        
        await session.execute(query, {
            "id": user_id,
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": hashed,
            "role": "admin",
            "is_active": True,
            "can_break_glass": False
        })
        
        await session.commit()
        print("User 'admin' created successfully.")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(create_user())
    except Exception as e:
        print(f"Error creating user: {e}")
        # Print traceback
        import traceback
        traceback.print_exc()
        sys.exit(1)
