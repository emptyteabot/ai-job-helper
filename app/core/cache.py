"""
性能优化 - 缓存系统
解决卡顿问题
"""
import json
import hashlib
from typing import Any, Optional
from datetime import datetime, timedelta

class SimpleCache:
    """简单内存缓存（生产环境建议用Redis）"""
    
    def __init__(self):
        self._cache = {}
        self._expire = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._expire:
            if datetime.now() > self._expire[key]:
                del self._cache[key]
                del self._expire[key]
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, expire_seconds: int = 3600):
        """设置缓存"""
        self._cache[key] = value
        self._expire[key] = datetime.now() + timedelta(seconds=expire_seconds)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expire:
            del self._expire[key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._expire.clear()
    
    def make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        data = json.dumps([args, kwargs], sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()

# 全局缓存实例
cache = SimpleCache()

def cached(expire_seconds: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{cache.make_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                print(f"✅ 缓存命中: {func.__name__}")
                return result
            
            # 执行函数
            print(f"🔄 缓存未命中，执行函数: {func.__name__}")
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator

# 使用示例
"""
from app.core.cache import cached

@cached(expire_seconds=1800)  # 缓存30分钟
async def analyze_resume(resume_text: str):
    # AI分析逻辑
    pass
"""

性能优化 - 缓存系统
解决卡顿问题
"""
import json
import hashlib
from typing import Any, Optional
from datetime import datetime, timedelta

class SimpleCache:
    """简单内存缓存（生产环境建议用Redis）"""
    
    def __init__(self):
        self._cache = {}
        self._expire = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._expire:
            if datetime.now() > self._expire[key]:
                del self._cache[key]
                del self._expire[key]
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, expire_seconds: int = 3600):
        """设置缓存"""
        self._cache[key] = value
        self._expire[key] = datetime.now() + timedelta(seconds=expire_seconds)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expire:
            del self._expire[key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._expire.clear()
    
    def make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        data = json.dumps([args, kwargs], sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()

# 全局缓存实例
cache = SimpleCache()

def cached(expire_seconds: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{cache.make_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                print(f"✅ 缓存命中: {func.__name__}")
                return result
            
            # 执行函数
            print(f"🔄 缓存未命中，执行函数: {func.__name__}")
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator

# 使用示例
"""
from app.core.cache import cached

@cached(expire_seconds=1800)  # 缓存30分钟
async def analyze_resume(resume_text: str):
    # AI分析逻辑
    pass
"""

性能优化 - 缓存系统
解决卡顿问题
"""
import json
import hashlib
from typing import Any, Optional
from datetime import datetime, timedelta

class SimpleCache:
    """简单内存缓存（生产环境建议用Redis）"""
    
    def __init__(self):
        self._cache = {}
        self._expire = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._expire:
            if datetime.now() > self._expire[key]:
                del self._cache[key]
                del self._expire[key]
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, expire_seconds: int = 3600):
        """设置缓存"""
        self._cache[key] = value
        self._expire[key] = datetime.now() + timedelta(seconds=expire_seconds)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expire:
            del self._expire[key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._expire.clear()
    
    def make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        data = json.dumps([args, kwargs], sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()

# 全局缓存实例
cache = SimpleCache()

def cached(expire_seconds: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{cache.make_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                print(f"✅ 缓存命中: {func.__name__}")
                return result
            
            # 执行函数
            print(f"🔄 缓存未命中，执行函数: {func.__name__}")
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator

# 使用示例
"""
from app.core.cache import cached

@cached(expire_seconds=1800)  # 缓存30分钟
async def analyze_resume(resume_text: str):
    # AI分析逻辑
    pass
"""

性能优化 - 缓存系统
解决卡顿问题
"""
import json
import hashlib
from typing import Any, Optional
from datetime import datetime, timedelta

class SimpleCache:
    """简单内存缓存（生产环境建议用Redis）"""
    
    def __init__(self):
        self._cache = {}
        self._expire = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._expire:
            if datetime.now() > self._expire[key]:
                del self._cache[key]
                del self._expire[key]
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, expire_seconds: int = 3600):
        """设置缓存"""
        self._cache[key] = value
        self._expire[key] = datetime.now() + timedelta(seconds=expire_seconds)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expire:
            del self._expire[key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._expire.clear()
    
    def make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        data = json.dumps([args, kwargs], sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()

# 全局缓存实例
cache = SimpleCache()

def cached(expire_seconds: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{cache.make_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                print(f"✅ 缓存命中: {func.__name__}")
                return result
            
            # 执行函数
            print(f"🔄 缓存未命中，执行函数: {func.__name__}")
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator

# 使用示例
"""
from app.core.cache import cached

@cached(expire_seconds=1800)  # 缓存30分钟
async def analyze_resume(resume_text: str):
    # AI分析逻辑
    pass
"""



