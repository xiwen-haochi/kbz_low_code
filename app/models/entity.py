"""
实体定义数据模型
用于低代码平台的动态实体管理
"""
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from sqlalchemy import (
    Column, 
    BigInteger, 
    String, 
    Text, 
    Boolean, 
    DateTime, 
    ForeignKey,
    Index,
    Enum as SQLEnum
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

from app.utils.snowflake import get_snowflake_id
from app.utils.db import Base


# 枚举定义
class FieldType(str, Enum):
    """字段类型枚举"""
    STRING = "string"           # 文本
    NUMBER = "number"           # 数字
    BOOLEAN = "boolean"         # 布尔值
    DATE = "date"              # 日期
    DATETIME = "datetime"       # 日期时间
    ENUM = "enum"              # 枚举选择
    RELATION = "relation"       # 关联关系
    ARRAY = "array"            # 数组
    JSON = "json"              # JSON对象
    TEXT = "text"              # 长文本
    EMAIL = "email"            # 邮箱
    URL = "url"                # 网址
    FILE = "file"              # 文件
    IMAGE = "image"            # 图片
    PASSWORD = "password"       # 密码
    PHONE = "phone"            # 电话
    ADDRESS = "address"        # 地址
    CURRENCY = "currency"      # 货币
    PERCENT = "percent"        # 百分比


class ValueType(str, Enum):
    """值类型枚举 - 用于区分单选、多选等"""
    SINGLE = "single"          # 单个值
    MULTIPLE = "multiple"      # 多个值
    SINGLE_SELECT = "single_select"    # 单选
    MULTI_SELECT = "multi_select"      # 多选
    CHECKBOX = "checkbox"      # 复选框
    RADIO = "radio"           # 单选按钮
    SWITCH = "switch"         # 开关
    SLIDER = "slider"         # 滑块
    CASCADER = "cascader"     # 级联选择
    TREE_SELECT = "tree_select"        # 树形选择
    TAG_INPUT = "tag_input"   # 标签输入
    RICH_TEXT = "rich_text"   # 富文本
    CODE = "code"             # 代码编辑器
    COLOR = "color"           # 颜色选择器
    UPLOAD = "upload"         # 文件上传
    RATING = "rating"         # 评分


class EntityStatus(str, Enum):
    """实体状态枚举"""
    ACTIVE = "active"         # 激活
    INACTIVE = "inactive"     # 未激活
    DRAFT = "draft"          # 草稿
    ARCHIVED = "archived"    # 已归档
    DELETED = "deleted"      # 已删除


class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )


class TenantMixin:
    """多租户混入类"""
    tenant_id = Column(
        BigInteger, 
        nullable=False, 
        comment="租户ID（多租户支持）"
    )


class EntityDefinition(Base, TimestampMixin, TenantMixin):
    """
    实体定义表
    定义可创建的实体类型，如用户、产品等
    """
    __tablename__ = "entity_definition"
    
    id = Column(
        BigInteger, 
        primary_key=True, 
        default=get_snowflake_id,
        comment="雪花算法生成的ID"
    )
    name = Column(
        String(100), 
        nullable=False, 
        comment="实体类型名称，如user、product"
    )
    display_name = Column(
        String(200), 
        nullable=False, 
        comment="显示名称，如用户、产品"
    )
    description = Column(
        Text, 
        nullable=True, 
        comment="描述信息"
    )
    is_system = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="是否系统内置"
    )
    is_enabled = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否启用"
    )
    meta = Column(
        JSON, 
        nullable=True, 
        comment="JSON格式的元数据，用于存储额外信息"
    )
    parent_id = Column(
        BigInteger, 
        ForeignKey('entity_definition.id', ondelete='SET NULL'),
        nullable=True,
        comment="父实体ID（用于树形结构）"
    )
    
    # 关系定义
    field_definitions = relationship(
        "FieldDefinition",
        back_populates="entity_definition",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    entity_data = relationship(
        "EntityData",
        back_populates="entity_definition",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_entity_def_name_tenant', 'name', 'tenant_id'),
        Index('idx_entity_def_enabled_tenant', 'is_enabled', 'tenant_id'),
        Index('idx_entity_def_system', 'is_system'),
        {'comment': '实体定义表'}
    )
    
    def __repr__(self):
        return f"<EntityDefinition(id={self.id}, name={self.name}, display_name={self.display_name})>"


class FieldDefinition(Base, TimestampMixin, TenantMixin):
    """
    字段定义表
    定义每种实体类型可拥有的字段
    """
    __tablename__ = "field_definition"
    
    id = Column(
        BigInteger, 
        primary_key=True, 
        default=get_snowflake_id,
        comment="雪花算法生成的ID"
    )
    entity_type_id = Column(
        BigInteger, 
        ForeignKey('entity_definition.id', ondelete='CASCADE'),
        nullable=False,
        comment="关联的实体类型ID"
    )
    name = Column(
        String(100), 
        nullable=False, 
        comment="字段名称"
    )
    display_name = Column(
        String(200), 
        nullable=False, 
        comment="显示名称"
    )
    field_type = Column(
        SQLEnum(FieldType), 
        nullable=False, 
        comment="字段类型(string/number/boolean/date/enum/relation等)"
    )
    value_type = Column(
        SQLEnum(ValueType),
        default=ValueType.SINGLE,
        nullable=False,
        comment="值类型(single/multiple/single_select/multi_select等)"
    )
    is_required = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="是否必填"
    )
    is_system = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="是否系统字段"
    )
    validation_rules = Column(
        JSON, 
        nullable=True, 
        comment="JSON格式的验证规则"
    )
    data_source = Column(
        JSON, 
        nullable=True, 
        comment="数据源设置（适用于下拉选择等）"
    )
    sort_order = Column(
        BigInteger,
        default=0,
        nullable=False,
        comment="排序顺序"
    )
    parent_id = Column(
        BigInteger, 
        ForeignKey('field_definition.id', ondelete='SET NULL'),
        nullable=True,
        comment="父字段ID（用于分组或层级）"
    )
    # 关系定义
    entity_definition = relationship(
        "EntityDefinition",
        back_populates="field_definitions"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_field_def_entity_type', 'entity_type_id'),
        Index('idx_field_def_name_entity', 'name', 'entity_type_id'),
        Index('idx_field_def_type', 'field_type'),
        Index('idx_field_def_required', 'is_required'),
        Index('idx_field_def_system', 'is_system'),
        Index('idx_field_def_tenant', 'tenant_id'),
        {'comment': '字段定义表'}
    )
    
    def __repr__(self):
        return f"<FieldDefinition(id={self.id}, name={self.name}, field_type={self.field_type})>"


class EntityData(Base, TimestampMixin, TenantMixin):
    """
    实体数据表
    存储所有实体的实际数据
    """
    __tablename__ = "entity_data"
    
    id = Column(
        BigInteger, 
        primary_key=True, 
        default=get_snowflake_id,
        comment="雪花算法生成的ID"
    )
    entity_type_id = Column(
        BigInteger, 
        ForeignKey('entity_definition.id', ondelete='CASCADE'),
        nullable=False,
        comment="实体类型ID"
    )
    data = Column(
        JSON, 
        nullable=False, 
        comment="JSON格式存储所有配置字段的值"
    )
    created_by = Column(
        BigInteger, 
        nullable=True, 
        comment="创建者ID"
    )
    updated_by = Column(
        BigInteger, 
        nullable=True, 
        comment="最后更新者ID"
    )
    version = Column(
        BigInteger, 
        default=1, 
        nullable=False,
        comment="版本号（用于乐观锁）"
    )
    status = Column(
        SQLEnum(EntityStatus), 
        default=EntityStatus.ACTIVE, 
        nullable=False,
        comment="状态"
    )
    meta = Column(
        JSON, 
        nullable=True, 
        comment="JSON格式的元数据，用于存储额外信息"
    )
    parent_id = Column(
        BigInteger, 
        ForeignKey('entity_data.id', ondelete='SET NULL'),
        nullable=True,
        comment="父实体ID（用于树形结构）"
    )
    # 关系定义
    entity_definition = relationship(
        "EntityDefinition",
        back_populates="entity_data"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_entity_data_type', 'entity_type_id'),
        Index('idx_entity_data_status', 'status'),
        Index('idx_entity_data_tenant', 'tenant_id'),
        Index('idx_entity_data_created_by', 'created_by'),
        Index('idx_entity_data_version', 'version'),
        Index('idx_entity_data_created_at', 'created_at'),
        # 复合索引用于常见查询
        Index('idx_entity_data_type_status_tenant', 'entity_type_id', 'status', 'tenant_id'),
        Index('idx_entity_data_type_tenant_created', 'entity_type_id', 'tenant_id', 'created_at'),
        {'comment': '实体数据表'}
    )
    
    def __repr__(self):
        return f"<EntityData(id={self.id}, entity_type_id={self.entity_type_id}, status={self.status})>"
    
    def get_field_value(self, field_name: str) -> Any:
        """
        获取指定字段的值
        
        Args:
            field_name: 字段名称
            
        Returns:
            字段值，如果字段不存在返回None
        """
        if self.data is None:
            return None
        
        data_dict = self.data if isinstance(self.data, dict) else {}
        
        if field_name not in data_dict:
            return None
        
        field_data = data_dict[field_name]
        if isinstance(field_data, dict) and 'value' in field_data:
            return field_data['value']
        
        return field_data
    
    def set_field_value(self, field_name: str, value: Any, field_type: Optional[str] = None, display: Optional[str] = None) -> None:
        """
        设置指定字段的值
        
        Args:
            field_name: 字段名称
            value: 字段值
            field_type: 字段类型
            display: 显示值
        """
        if self.data is None:
            self.data = {}
        
        data_dict = self.data if isinstance(self.data, dict) else {}
        
        field_data = {
            "value": value,
            "meta": {
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        if field_type:
            field_data["type"] = field_type
            
        if display:
            field_data["display"] = display
            
        data_dict[field_name] = field_data
        self.data = data_dict
    
    def get_all_field_values(self) -> Dict[str, Any]:
        """
        获取所有字段的值
        
        Returns:
            字段名到值的映射
        """
        if self.data is None:
            return {}
        
        data_dict = self.data if isinstance(self.data, dict) else {}
        
        result = {}
        for field_name, field_data in data_dict.items():
            if isinstance(field_data, dict) and 'value' in field_data:
                result[field_name] = field_data['value']
            else:
                result[field_name] = field_data
        
        return result


# 辅助函数
def create_field_validation_rule(
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    pattern: Optional[str] = None,
    enum_values: Optional[list] = None,
    required: bool = False
) -> Dict[str, Any]:
    """
    创建字段验证规则
    
    Args:
        min_length: 最小长度
        max_length: 最大长度
        min_value: 最小值
        max_value: 最大值
        pattern: 正则表达式模式
        enum_values: 枚举值列表
        required: 是否必填
        
    Returns:
        验证规则字典
    """
    rule: Dict[str, Any] = {"required": required}
    
    if min_length is not None:
        rule["min_length"] = min_length
    if max_length is not None:
        rule["max_length"] = max_length
    if min_value is not None:
        rule["min_value"] = min_value
    if max_value is not None:
        rule["max_value"] = max_value
    if pattern is not None:
        rule["pattern"] = pattern
    if enum_values is not None:
        rule["enum_values"] = enum_values
    
    return rule


def create_data_source_config(
    source_type: str,
    source_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    创建数据源配置
    
    Args:
        source_type: 数据源类型 (static/api/sql/entity)
        source_config: 数据源配置
        
    Returns:
        数据源配置字典
    """
    return {
        "type": source_type,
        "config": source_config
    }

