#!/usr/bin/env python3
"""
First-time setup script for Clinical Care Tools.

Creates:
- Admin user (if not exists)
- Initial database setup

Usage:
    python scripts/first-time-setup.py

Environment Variables:
    ADMIN_USERNAME: Admin username (default: admin)
    ADMIN_PASSWORD: Admin password (default: admin123 - CHANGE IN PRODUCTION!)
    ADMIN_FULL_NAME: Admin full name (default: System Administrator)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models.user import User


async def create_admin_user(db: AsyncSession) -> bool:
    """
    Create admin user if not exists.

    Returns:
        True if user was created, False if already exists
    """
    # Get admin credentials from environment
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_full_name = os.getenv("ADMIN_FULL_NAME", "System Administrator")

    # Check if admin user already exists
    result = await db.execute(
        select(User).where(User.username == admin_username)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print(f"ℹ️  Admin user '{admin_username}' already exists (ID: {existing_user.id})")
        return False

    # Hash password using bcrypt
    password_bytes = admin_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # Create admin user
    admin_user = User(
        username=admin_username,
        full_name=admin_full_name,
        hashed_password=hashed_password,
        role="admin",  # admin role has all permissions
        is_active=True,
        must_change_password=False  # Allow admin to keep default password (they can change later)
    )

    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    print(f"✅ Created admin user '{admin_username}' (ID: {admin_user.id})")
    print(f"   Full Name: {admin_full_name}")
    print(f"   Role: {admin_user.role}")
    print(f"   Password: {'*' * len(admin_password)} (set via ADMIN_PASSWORD env var)")

    if admin_password == "admin123":
        print()
        print("⚠️  WARNING: Using default password 'admin123'")
        print("   Please change this immediately in production!")
        print("   Set ADMIN_PASSWORD environment variable to use a different password")

    return True


async def verify_database_connection():
    """Verify database connection is working."""
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check DATABASE_URL environment variable")
        print("3. Run migrations: alembic upgrade head")
        return False


async def check_migrations():
    """Check if database tables exist."""
    try:
        async with AsyncSessionLocal() as db:
            # Try to query users table
            await db.execute(select(User).limit(1))
        print("✅ Database tables exist (migrations applied)")
        return True
    except Exception as e:
        print(f"❌ Database tables missing: {e}")
        print()
        print("Please run migrations first:")
        print("  cd /home/user/cogstack-nlp/clinical-care-tools/backend")
        print("  alembic upgrade head")
        return False


async def main():
    """Main setup function."""
    print("=" * 70)
    print("Clinical Care Tools - First-Time Setup")
    print("=" * 70)
    print()

    # Step 1: Verify database connection
    print("Step 1: Verifying database connection...")
    if not await verify_database_connection():
        sys.exit(1)
    print()

    # Step 2: Check migrations
    print("Step 2: Checking database migrations...")
    if not await check_migrations():
        sys.exit(1)
    print()

    # Step 3: Create admin user
    print("Step 3: Creating admin user...")
    async with AsyncSessionLocal() as db:
        created = await create_admin_user(db)
    print()

    # Summary
    print("=" * 70)
    if created:
        print("✅ First-time setup complete!")
        print()
        print("Next steps:")
        print("1. Start the backend server:")
        print("   cd /home/user/cogstack-nlp/clinical-care-tools/backend")
        print("   uvicorn app.main:app --reload --port 8000")
        print()
        print("2. Login with admin credentials:")
        print(f"   Username: {os.getenv('ADMIN_USERNAME', 'admin')}")
        print(f"   Password: {os.getenv('ADMIN_PASSWORD', 'admin123')}")
        print()
        print("3. Access API docs:")
        print("   http://localhost:8000/docs")
    else:
        print("✅ Setup verification complete!")
        print()
        print("Admin user already exists. System is ready to use.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
