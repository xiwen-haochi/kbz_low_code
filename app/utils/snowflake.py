import threading
import time
from queue import Queue, Empty
from datetime import datetime
import ipaddress

from app.config import settings


class SnowflakeIDGenerator:
    """
    雪花算法ID生成器

    64位ID结构:
    - 1位符号位，始终为0
    - 41位时间戳（毫秒级，可使用69年）
    - 5位数据中心ID
    - 5位工作机器ID
    - 12位序列号（毫秒内）
    """

    # 定义常量，提高性能
    WORKER_ID_BITS = 5
    DATACENTER_ID_BITS = 5
    SEQUENCE_BITS = 12

    # 最大值计算
    MAX_WORKER_ID = -1 ^ (-1 << WORKER_ID_BITS)  # 31
    MAX_DATACENTER_ID = -1 ^ (-1 << DATACENTER_ID_BITS)  # 31
    MAX_SEQUENCE = -1 ^ (-1 << SEQUENCE_BITS)  # 4095

    # 位移计算
    WORKER_ID_SHIFT = SEQUENCE_BITS  # 12
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS  # 17
    TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS  # 22

    # 开始时间戳 (2020-01-01 00:00:00 UTC)
    EPOCH = 1577836800000

    def __init__(self, worker_id, datacenter_id=0, batch_size=1000):
        """
        初始化雪花ID生成器

        Args:
            worker_id: 工作机器ID (0-31)
            datacenter_id: 数据中心ID (0-31)
            batch_size: 批量生成的ID数量
        """
        # 参数校验
        if worker_id > self.MAX_WORKER_ID or worker_id < 0:
            raise ValueError(f"worker_id必须在0和{self.MAX_WORKER_ID}之间")
        if datacenter_id > self.MAX_DATACENTER_ID or datacenter_id < 0:
            raise ValueError(f"datacenter_id必须在0和{self.MAX_DATACENTER_ID}之间")

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = 0
        self.last_timestamp = -1
        self.batch_size = batch_size
        self.id_pool = []
        self.lock = threading.Lock()  # 用于线程安全

    def _get_timestamp(self):
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp):
        """等待到下一毫秒"""
        timestamp = self._get_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._get_timestamp()
        return timestamp

    def _next_id(self):
        """生成下一个ID"""
        timestamp = self._get_timestamp()

        # 时钟回拨检测
        if timestamp < self.last_timestamp:
            # 时钟回拨处理策略: 等待时钟赶上
            timestamp = self._wait_next_millis(self.last_timestamp)

        # 同一毫秒内，序列号递增
        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
            # 序列号溢出，等待下一毫秒
            if self.sequence == 0:
                timestamp = self._wait_next_millis(self.last_timestamp)
        else:
            # 新的毫秒，序列号重置
            self.sequence = 0

        self.last_timestamp = timestamp

        # 生成64位ID
        return (
            ((timestamp - self.EPOCH) << self.TIMESTAMP_SHIFT)
            | (self.datacenter_id << self.DATACENTER_ID_SHIFT)
            | (self.worker_id << self.WORKER_ID_SHIFT)
            | self.sequence
        )

    def _generate_batch(self):
        """批量生成ID并缓存"""
        with self.lock:
            ids = []
            for _ in range(self.batch_size):
                ids.append(self._next_id())
            return ids

    def get_id(self):
        """从池中获取ID，池空时自动补充"""
        with self.lock:
            if not self.id_pool:
                self.id_pool = self._generate_batch()
            return self.id_pool.pop(0)

    def parse_id(self, snowflake_id):
        """
        解析雪花ID，返回其组成部分
        """
        timestamp = (snowflake_id >> self.TIMESTAMP_SHIFT) + self.EPOCH
        datacenter_id = (snowflake_id >> self.DATACENTER_ID_SHIFT) & (
            (1 << self.DATACENTER_ID_BITS) - 1
        )
        worker_id = (snowflake_id >> self.WORKER_ID_SHIFT) & (
            (1 << self.WORKER_ID_BITS) - 1
        )
        sequence = snowflake_id & ((1 << self.SEQUENCE_BITS) - 1)

        # 转换时间戳为可读格式
        datetime_obj = datetime.fromtimestamp(timestamp / 1000)

        return {
            "timestamp": timestamp,
            "datetime": datetime_obj.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "datacenter_id": datacenter_id,
            "worker_id": worker_id,
            "sequence": sequence,
        }


class AsyncSnowflakeGenerator:
    """
    异步雪花ID生成器

    使用后台线程预填充ID池，以提高性能
    """

    def __init__(self, worker_id, datacenter_id=0, pool_size=1000, min_threshold=100):
        """
        初始化异步ID生成器

        Args:
            worker_id: 工作机器ID
            datacenter_id: 数据中心ID
            pool_size: ID池最大容量
            min_threshold: 补充ID的阈值
        """
        self.generator = SnowflakeIDGenerator(worker_id, datacenter_id)
        self.id_pool = Queue(maxsize=pool_size)
        self.min_threshold = min_threshold
        self.refill_thread = threading.Thread(target=self._refill_pool, daemon=True)
        self.refill_thread.start()

    def _refill_pool(self):
        """后台线程，持续补充ID池"""
        while True:
            if self.id_pool.qsize() < self.min_threshold:
                print(f"ID池低于阈值，当前大小: {self.id_pool.qsize()}, 正在补充...")
                batch = self.generator._generate_batch()
                for id in batch:
                    if not self.id_pool.full():
                        self.id_pool.put(id)
            time.sleep(0.1)  # 避免CPU过度使用

    def get_id(self):
        """从池中获取ID，非阻塞"""
        try:
            return self.id_pool.get_nowait()
        except Empty:
            # 池空时直接生成一个（应该很少发生）
            return self.generator._next_id()

    def parse_id(self, snowflake_id):
        """解析ID"""
        return self.generator.parse_id(snowflake_id)


def _get_worker_id_from_ip():
    """根据IP地址生成worker_id"""
    try:
        import socket

        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        # 使用IP地址的最后一部分作为worker_id
        if isinstance(ip_obj, ipaddress.IPv4Address):
            return ip_obj.packed[-1] % 32
        else:
            return ip_obj.packed[-1] % 32
    except Exception:
        # 出错时使用随机数
        import random

        return random.randint(0, 31)


# 启动时从配置或环境变量获取worker_id
def _create_id_generator():
    """
    创建并返回一个雪花ID生成器实例
    优先使用环境变量配置，然后尝试自动生成
    """
    worker_id = int(settings.SNOWFLAKE_WORKER_ID)
    datacenter_id = int(settings.SNOWFLAKE_DATACENTER_ID)
    # worker_id = int(1)
    # datacenter_id = int(1)

    # 如果未配置worker_id，则自动生成
    if worker_id == 0:
        worker_id = _get_worker_id_from_ip()

    # 创建并返回生成器实例
    return AsyncSnowflakeGenerator(
        worker_id=worker_id, datacenter_id=datacenter_id, pool_size=1000
    )

id_generator = _create_id_generator()

def get_snowflake_id():
    """
    获取一个雪花ID
    """
    return id_generator.get_id()