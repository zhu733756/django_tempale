import time
import uuid
from threading import Thread
from django_redis import get_redis_connection

redis_db = get_redis_connection("default")

#获取一个锁
# lock_name：锁定名称
# acquire_time: 客户端等待获取锁的时间
# time_out: 锁的超时时间
def acquire_lock(lock_name, acquire_time=10, time_out=10):
    """获取一个分布式锁"""
    identifier = str(uuid.uuid4())
    end = time.time() + acquire_time
    lock = "lock:" + lock_name
    while time.time() < end:
        if redis_db.setnx(lock, identifier):
            # 给锁设置超时时间, 防止进程崩溃导致其他进程无法获取锁
            redis_db.expire(lock, time_out)
            return identifier
        elif not redis_db.ttl(lock):
            redis_db.expire(lock, time_out)
        time.sleep(0.001)
    return False

#释放一个锁
def release_lock(lock_name, identifier):
    """通用的锁释放函数"""
    lock = "lock:" + lock_name
    pip = redis_db.pipeline(True)
    while True:
        try:
            pip.watch(lock)
            lock_value = redis_db.get(lock)
            if not lock_value:
                return True

            if lock_value.decode() == identifier:
                pip.multi()
                pip.delete(lock)
                pip.execute()
                return True
            pip.unwatch()
            break
        except redis.excetions.WacthcError:
            pass
    return False