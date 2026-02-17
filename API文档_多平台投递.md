# 多平台投递 API 文档

## 概述

统一的多平台自动投递接口，支持 Boss直聘、智联招聘、LinkedIn 三大平台。

## 核心功能

### 1. 统一投递接口
- 支持多平台并发投递
- 任务队列管理
- 失败重试机制
- 实时进度推送

### 2. 平台支持
- **Boss直聘**: 手机验证码登录
- **智联招聘**: 账号密码登录
- **LinkedIn**: Easy Apply + AI 问答

### 3. 数据统计
- 投递记录存储
- 统计数据聚合
- 历史查询接口

---

## API 接口

### 1. 获取支持的平台列表

```http
GET /api/auto-apply/platforms
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "platforms": [
      {
        "id": "boss",
        "name": "Boss直聘",
        "icon": "💼",
        "status": "available",
        "features": ["手机验证码登录", "智能投递", "打招呼语"],
        "config_fields": [
          {"name": "phone", "label": "手机号", "type": "text", "required": true}
        ]
      },
      {
        "id": "zhilian",
        "name": "智联招聘",
        "icon": "📋",
        "status": "available",
        "features": ["账号密码登录", "简历投递", "附件上传"],
        "config_fields": [
          {"name": "username", "label": "用户名", "type": "text", "required": true},
          {"name": "password", "label": "密码", "type": "password", "required": true}
        ]
      },
      {
        "id": "linkedin",
        "name": "LinkedIn",
        "icon": "🔗",
        "status": "available",
        "features": ["Easy Apply", "AI问答", "国际职位"],
        "config_fields": [
          {"name": "email", "label": "邮箱", "type": "email", "required": true},
          {"name": "password", "label": "密码", "type": "password", "required": true}
        ]
      }
    ]
  }
}
```

---

### 2. 启动多平台投递

```http
POST /api/auto-apply/start-multi
```

**请求体:**
```json
{
  "platforms": ["boss", "zhilian", "linkedin"],
  "config": {
    "keywords": "Python开发",
    "location": "北京",
    "max_count": 50,
    "blacklist": ["字节跳动", "腾讯"],
    "headless": false,
    "use_ai_answers": true,
    "boss_config": {
      "phone": "13800138000"
    },
    "zhilian_config": {
      "username": "user@example.com",
      "password": "password123"
    },
    "linkedin_config": {
      "email": "user@example.com",
      "password": "password123"
    }
  }
}
```

**参数说明:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platforms | array | 是 | 要投递的平台列表 |
| config.keywords | string | 是 | 搜索关键词 |
| config.location | string | 是 | 工作地点 |
| config.max_count | number | 否 | 每个平台最大投递数量（默认50） |
| config.blacklist | array | 否 | 公司黑名单 |
| config.headless | boolean | 否 | 是否无头模式（默认false） |
| config.use_ai_answers | boolean | 否 | 是否使用AI回答问题（默认true） |
| config.{platform}_config | object | 是 | 各平台特定配置 |

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "已启动 3 个平台的自动投递"
  }
}
```

---

### 3. 启动单平台投递

```http
POST /api/auto-apply/start
```

**请求体:**
```json
{
  "platform": "linkedin",
  "keywords": "Python开发",
  "location": "北京",
  "max_count": 50,
  "blacklist": ["字节跳动"],
  "user_profile": {
    "email": "user@example.com",
    "password": "password123"
  },
  "headless": false,
  "pause_before_submit": false
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "自动投递任务已启动"
  }
}
```

---

### 4. 查询任务状态

```http
GET /api/auto-apply/status/{task_id}
```

**响应示例（单平台）:**
```json
{
  "success": true,
  "data": {
    "task": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "running",
      "config": {...},
      "progress": {
        "applied": 15,
        "failed": 2,
        "total": 50,
        "current_job": "Python高级开发工程师"
      },
      "created_at": "2026-02-17T10:00:00",
      "started_at": "2026-02-17T10:00:05",
      "completed_at": null
    }
  }
}
```

**响应示例（多平台）:**
```json
{
  "success": true,
  "data": {
    "task": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "running",
      "platforms": ["boss", "zhilian", "linkedin"],
      "progress": {
        "total_platforms": 3,
        "completed_platforms": 1,
        "total_applied": 25,
        "total_failed": 3,
        "platform_progress": {
          "boss": {
            "status": "completed",
            "total": 30,
            "applied": 25,
            "failed": 5
          },
          "zhilian": {
            "status": "running",
            "total": 40,
            "applied": 15,
            "failed": 2
          },
          "linkedin": {
            "status": "pending",
            "total": 0,
            "applied": 0,
            "failed": 0
          }
        }
      },
      "created_at": "2026-02-17T10:00:00",
      "started_at": "2026-02-17T10:00:05",
      "completed_at": null
    }
  }
}
```

**状态说明:**
- `starting`: 任务启动中
- `running`: 任务运行中
- `completed`: 任务已完成
- `failed`: 任务失败
- `stopped`: 任务已停止

---

### 5. 停止任务

```http
POST /api/auto-apply/stop
```

**请求体:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "message": "停止指令已发送"
  }
}
```

---

### 6. 获取投递历史

```http
GET /api/auto-apply/history?limit=50
```

**参数:**
- `limit`: 返回数量限制（默认50）

**响应示例:**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "platforms": ["boss", "zhilian"],
        "progress": {...},
        "created_at": "2026-02-17T10:00:00",
        "completed_at": "2026-02-17T10:30:00"
      }
    ],
    "total": 10
  }
}
```

---

### 7. 获取统计数据

```http
GET /api/auto-apply/stats
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "total_tasks": 10,
    "completed_tasks": 8,
    "running_tasks": 2,
    "total_applied": 250,
    "total_failed": 30,
    "success_rate": 89.29,
    "platform_stats": {
      "boss": {
        "applied": 100,
        "failed": 10,
        "total": 150
      },
      "zhilian": {
        "applied": 80,
        "failed": 12,
        "total": 120
      },
      "linkedin": {
        "applied": 70,
        "failed": 8,
        "total": 100
      }
    }
  }
}
```

---

### 8. 测试平台配置

```http
POST /api/auto-apply/test-platform
```

**请求体:**
```json
{
  "platform": "boss",
  "config": {
    "phone": "13800138000"
  }
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "platform": "boss",
    "login_test": {
      "success": true,
      "message": "配置正确，手机号: 138****0000"
    },
    "config_valid": true
  }
}
```

---

## WebSocket 实时进度

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/auto-apply/{task_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('进度更新:', data);
};
```

### 消息类型

**1. 进度更新 (type: progress)**
```json
{
  "type": "progress",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "platforms": ["boss", "zhilian", "linkedin"],
  "progress": {
    "total_platforms": 3,
    "completed_platforms": 1,
    "total_applied": 25,
    "total_failed": 3,
    "platform_progress": {...}
  },
  "timestamp": "2026-02-17T10:05:00"
}
```

**2. 任务完成 (type: complete)**
```json
{
  "type": "complete",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": {...},
  "result": {...},
  "error": null
}
```

**3. 错误 (type: error)**
```json
{
  "type": "error",
  "message": "任务不存在"
}
```

---

## 使用示例

### Python

```python
import requests
import json

# 1. 启动多平台投递
response = requests.post(
    'http://localhost:8000/api/auto-apply/start-multi',
    json={
        'platforms': ['boss', 'zhilian'],
        'config': {
            'keywords': 'Python开发',
            'location': '北京',
            'max_count': 30,
            'boss_config': {'phone': '13800138000'},
            'zhilian_config': {
                'username': 'user@example.com',
                'password': 'password123'
            }
        }
    }
)

task_id = response.json()['data']['task_id']
print(f'任务已创建: {task_id}')

# 2. 查询进度
import time
while True:
    response = requests.get(f'http://localhost:8000/api/auto-apply/status/{task_id}')
    task = response.json()['data']['task']
    print(f"状态: {task['status']}, 已投递: {task['progress']['total_applied']}")

    if task['status'] in ['completed', 'failed', 'stopped']:
        break

    time.sleep(5)
```

### JavaScript

```javascript
// 1. 启动多平台投递
const response = await fetch('http://localhost:8000/api/auto-apply/start-multi', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    platforms: ['boss', 'zhilian'],
    config: {
      keywords: 'Python开发',
      location: '北京',
      max_count: 30,
      boss_config: {phone: '13800138000'},
      zhilian_config: {
        username: 'user@example.com',
        password: 'password123'
      }
    }
  })
});

const {task_id} = (await response.json()).data;
console.log('任务已创建:', task_id);

// 2. WebSocket 监听进度
const ws = new WebSocket(`ws://localhost:8000/ws/auto-apply/${task_id}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'progress') {
    console.log('进度:', data.progress);
  } else if (data.type === 'complete') {
    console.log('任务完成:', data.progress);
    ws.close();
  }
};
```

---

## 性能指标

- **API 响应时间**: < 100ms
- **并发支持**: >= 10 个任务
- **成功率**: >= 90%
- **内存占用**: < 500MB

---

## 错误处理

所有 API 返回统一的错误格式：

```json
{
  "success": false,
  "error": "错误信息",
  "code": 400
}
```

**常见错误码:**
- `400`: 请求参数错误
- `404`: 任务不存在
- `500`: 服务器内部错误

---

## 注意事项

1. **登录凭证**: 请妥善保管登录凭证，建议使用环境变量
2. **投递频率**: 建议控制投递频率，避免被平台限制
3. **黑名单**: 合理使用黑名单功能，避免重复投递
4. **无头模式**: 生产环境建议使用无头模式（headless: true）
5. **AI 问答**: LinkedIn 平台建议开启 AI 问答功能

---

## 测试

运行测试脚本：

```bash
python test_multi_platform_api.py
```

测试内容：
- ✅ 获取平台列表
- ✅ 测试平台配置
- ✅ 获取统计数据
- ✅ API 接口调用

---

## 更新日志

### v1.0.0 (2026-02-17)
- ✨ 新增多平台统一投递接口
- ✨ 支持 Boss直聘、智联招聘、LinkedIn
- ✨ 实时进度推送（WebSocket）
- ✨ 任务队列管理
- ✨ 统计数据聚合
- ✨ 平台配置测试接口
