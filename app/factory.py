"""
应用程序创建
"""
from fastapi import FastAPI, Depends

from app.utils.snowflake import get_snowflake_id
from app.config import settings
from app.api import api_router
from app.utils.helpers import setup_logging, setup_cors, lifespan

def create_application() -> FastAPI:
    """创建FastAPI应用"""
    # 设置日志
    setup_logging()
    
    # 创建应用
    app = FastAPI(
        title="kzb_low_code",
        description="低代码",
        lifespan=lifespan,
        version="0.1.0",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        debug=settings.DEBUG
    )
    
    # 配置CORS
    setup_cors(app)
    
    # 包含API路由
    app.include_router(api_router)
    
    # 添加健康检查端点
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok"}
    
    @app.get("/snowflake", tags=["雪花ID"], summary="获取雪花ID")
    async def get_snowflake(snowflake_id: int = Depends(get_snowflake_id, use_cache=False)):
        """获取一个雪花ID"""
        print(f"生成的雪花ID: {snowflake_id}")
        # 再次调用获取新ID进行比较
        another_id = get_snowflake_id()
        print(f"再次生成的ID: {another_id}")
        return {"snowflake_id": snowflake_id, "another_id": another_id}

    
    return app
