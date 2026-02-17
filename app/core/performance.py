"""
性能监控 - 实时监控系统性能
"""
import time
import psutil
from datetime import datetime
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0
    
    def record_request(self, response_time: float, is_error: bool = False):
        """记录请求"""
        self.request_count += 1
        self.total_response_time += response_time
        if is_error:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self.start_time
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2),
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate": round(self.error_count / self.request_count * 100, 2) if self.request_count > 0 else 0,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "requests_per_second": round(self.request_count / uptime, 2) if uptime > 0 else 0,
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "timestamp": datetime.now().isoformat()
        }

# 全局监控实例
monitor = PerformanceMonitor()

def track_performance(func):
    """性能追踪装饰器"""
    async def wrapper(*args, **kwargs):
        start = time.time()
        error = False
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            error = True
            raise e
        finally:
            response_time = time.time() - start
            monitor.record_request(response_time, error)
    return wrapper

性能监控 - 实时监控系统性能
"""
import time
import psutil
from datetime import datetime
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0
    
    def record_request(self, response_time: float, is_error: bool = False):
        """记录请求"""
        self.request_count += 1
        self.total_response_time += response_time
        if is_error:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self.start_time
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2),
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate": round(self.error_count / self.request_count * 100, 2) if self.request_count > 0 else 0,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "requests_per_second": round(self.request_count / uptime, 2) if uptime > 0 else 0,
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "timestamp": datetime.now().isoformat()
        }

# 全局监控实例
monitor = PerformanceMonitor()

def track_performance(func):
    """性能追踪装饰器"""
    async def wrapper(*args, **kwargs):
        start = time.time()
        error = False
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            error = True
            raise e
        finally:
            response_time = time.time() - start
            monitor.record_request(response_time, error)
    return wrapper

性能监控 - 实时监控系统性能
"""
import time
import psutil
from datetime import datetime
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0
    
    def record_request(self, response_time: float, is_error: bool = False):
        """记录请求"""
        self.request_count += 1
        self.total_response_time += response_time
        if is_error:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self.start_time
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2),
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate": round(self.error_count / self.request_count * 100, 2) if self.request_count > 0 else 0,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "requests_per_second": round(self.request_count / uptime, 2) if uptime > 0 else 0,
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "timestamp": datetime.now().isoformat()
        }

# 全局监控实例
monitor = PerformanceMonitor()

def track_performance(func):
    """性能追踪装饰器"""
    async def wrapper(*args, **kwargs):
        start = time.time()
        error = False
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            error = True
            raise e
        finally:
            response_time = time.time() - start
            monitor.record_request(response_time, error)
    return wrapper

性能监控 - 实时监控系统性能
"""
import time
import psutil
from datetime import datetime
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0
    
    def record_request(self, response_time: float, is_error: bool = False):
        """记录请求"""
        self.request_count += 1
        self.total_response_time += response_time
        if is_error:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self.start_time
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2),
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate": round(self.error_count / self.request_count * 100, 2) if self.request_count > 0 else 0,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "requests_per_second": round(self.request_count / uptime, 2) if uptime > 0 else 0,
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "timestamp": datetime.now().isoformat()
        }

# 全局监控实例
monitor = PerformanceMonitor()

def track_performance(func):
    """性能追踪装饰器"""
    async def wrapper(*args, **kwargs):
        start = time.time()
        error = False
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            error = True
            raise e
        finally:
            response_time = time.time() - start
            monitor.record_request(response_time, error)
    return wrapper



