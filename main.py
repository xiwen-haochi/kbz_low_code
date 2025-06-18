import uvicorn

from app.factory import create_application
from app.config import settings

# 创建应用实例
app = create_application()

if __name__ == "__main__":
    # 直接运行时使用Uvicorn服务器
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "error",
    )