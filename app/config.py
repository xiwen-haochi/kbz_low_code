"""
配置文件加载模块
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(env_prefix='KBZ_', env_file='.env', case_sensitive=True)
    # 服务配置
    API_HOST: str = Field(default="0.0.0.0", description="API服务的主机地址")
    API_PORT: int = Field(default=8000, description="API服务的端口号")
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key"
    
    SNOWFLAKE_DATACENTER_ID: int = Field(default=0, description="雪花算法数据中心ID")
    SNOWFLAKE_WORKER_ID: int = Field(default=0, description="雪花算法工作机器ID")
    
    # 数据库
    SQLALCHEMY_DATABASE_URI: str = Field(default="", description="MySQL数据库连接URL")
    REDIS_URL: str = Field(default="", description="Redis连接URL")
    
    
    

# 创建全局设置实例
settings = Settings()

# print("Settings loaded:", settings.model_dump())  # 调试输出，确认设置加载成功

