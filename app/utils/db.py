"""
数据库连接模块
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,
    future=True,
)


# 创建异步会话工厂
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基础模型类
Base = declarative_base()


# 获取数据库会话
async def get_db():
    """异步数据库会话依赖"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
