"""
Seeding script to initialize the database with a default tenant and admin user.
Run with: python -m backend.scripts.seed_db
"""
import asyncio
import logging
import sys
import os

# Add the project root to sys.path so we can import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from backend.database import init_db, async_session
from backend.models.user import Tenant, User
from backend.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed():
    logger.info("Starting database seeding...")
    
    # Ensure tables are created
    await init_db()
    
    async with async_session() as session:
        async with session.begin():
            # 1. Create Default Tenant if not exists
            tenant_slug = "default"
            result = await session.execute(select(Tenant).where(Tenant.slug == tenant_slug))
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                tenant = Tenant(
                    name="Default Organization",
                    slug=tenant_slug,
                    is_active=True
                )
                session.add(tenant)
                await session.flush()
                logger.info("Created default tenant: %s", tenant_slug)
            else:
                logger.info("Tenant %s already exists", tenant_slug)
            
            # 2. Create Admin User if not exists
            admin_email = "admin@agentforge.ai"
            result = await session.execute(select(User).where(User.email == admin_email))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    tenant_id=tenant.id,
                    email=admin_email,
                    hashed_password=hash_password("admin123"),
                    full_name="System Admin",
                    role="admin",
                    is_active=True
                )
                session.add(user)
                logger.info("Created admin user: %s (password: admin123)", admin_email)
            else:
                logger.info("Admin user %s already exists", admin_email)
                
    logger.info("Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
