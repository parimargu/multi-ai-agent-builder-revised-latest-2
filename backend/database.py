"""
Database engine and session management for AgentForge.
Uses SQLAlchemy async engine with PostgreSQL.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from backend.config import get_config

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


config = get_config()

def create_engine_instance():
    """Create the SQLAlchemy engine based on configuration."""
    url = config.database_url
    logger.info("Initializing database engine (type: %s)", config.database_type)
    
    if config.database_type == "sqlite":
        # SQLite doesn't support pool_size/max_overflow in typical async setup
        from sqlalchemy.pool import StaticPool
        return create_async_engine(
            url,
            echo=config.get("database.echo", False),
            poolclass=StaticPool, # Useful for in-memory or single-connection
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL support
        return create_async_engine(
            url,
            echo=config.get("database.echo", False),
            pool_size=config.get("database.pool_size", 20),
            max_overflow=config.get("database.max_overflow", 10),
        )

engine = create_engine_instance()

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency that yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup with improved error handling."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables initialized successfully (%s)", config.database_type)
    except Exception as e:
        logger.error("❌ Database initialization FAILED: %s", str(e))
        if "Connect call failed" in str(e) or "Connection refused" in str(e):
            logger.warning("HINT: It looks like your database server (PostgreSQL) is not running.")
            logger.warning("      You can switch to SQLite by setting 'database.type: sqlite' in app_config.yaml")
        raise


async def close_db():
    """Dispose engine on shutdown."""
    await engine.dispose()
    logger.info("Database connection closed")
