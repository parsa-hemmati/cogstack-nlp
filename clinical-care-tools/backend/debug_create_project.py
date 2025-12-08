
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.project import Project, ProjectMember, ProjectMemberRole
from app.models.user import User
from sqlalchemy import select
import uuid
import traceback
from app.services.audit_service import log_action

async def debug_create():
    print("Starting Debug Script...")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Get Admin User
            print("Fetching admin user...")
            result = await db.execute(select(User).where(User.username == 'admin'))
            user = result.scalar_one_or_none()
            if not user:
                print("Admin user not found!")
                return
            
            print(f"User found: {user.id}")

            # 2. Try simple insert to Project (Bypass Service)
            print("Attempting to insert Project...")
            pid = uuid.uuid4()
            p = Project(id=pid, name="Debug Project", description="Debug", created_by=user.id)
            db.add(p)
            await db.flush() # Flush to check constraints
            print(f"Project flushed successfully. ID: {pid}")
            
            # 3. Try ProjectMember
            print("Attempting to insert ProjectMember...")
            m = ProjectMember(project_id=pid, user_id=user.id, role=ProjectMemberRole.OWNER, added_by=user.id)
            db.add(m)
            await db.flush()
            print("ProjectMember flushed successfully.")

            # Commit the project/member transaction
            await db.commit()
            print("Transaction committed.")
            
            # 4. Audit Log
            print("Attempting log_action...")
            # Re-acquire session or continue? Continue is fine.
            # But wait, audit_logs schema might be the issue.
            await log_action(
                db=db,
                user_id=str(user.id),
                username=user.username,
                action="DEBUG_ACTION",
                resource_type="project",
                resource_id=str(pid),
                ip_address="127.0.0.1",
                user_agent="debug-script",
                details={"foo": "bar"}
            )
            print("AuditLog created successfully.")
            
        except Exception:
            print("EXCEPTION OCCURRED:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_create())
