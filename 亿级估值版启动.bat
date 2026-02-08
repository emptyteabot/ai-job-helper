@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    AI求职助手 - 亿级估值版本启动
echo ========================================
echo.
echo 🚀 产品定位: 对标DeepSeek APP
echo 💰 目标估值: $100M - $500M
echo 🎯 核心优势: Multi-Agent + 真实数据
echo.
echo ========================================
echo.

echo [1/4] 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python环境正常
echo.

echo [2/4] 检查依赖包...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo ⚠️  正在安装依赖包...
    pip install fastapi uvicorn python-multipart python-dotenv openai PyPDF2 python-docx pillow pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple
)
echo ✅ 依赖包检查完成
echo.

echo [3/4] 检查配置文件...
if not exist .env (
    echo ⚠️  未找到.env文件，创建示例配置...
    echo DEEPSEEK_API_KEY=your_api_key_here > .env
    echo ⚠️  请在.env文件中配置您的DeepSeek API Key
)
echo ✅ 配置文件检查完成
echo.

echo [4/4] 启动Web服务...
echo.
echo ========================================
echo    🌐 访问地址
echo ========================================
echo.
echo 📍 官网首页: http://localhost:8000
echo 📍 应用页面: http://localhost:8000/app
echo 📍 API文档: http://localhost:8000/docs
echo.
echo ========================================
echo    ✨ 核心功能
echo ========================================
echo.
echo ✅ Multi-Agent协作 (6个AI)
echo ✅ 技能图谱匹配
echo ✅ 真实岗位数据 (1000+)
echo ✅ 简历深度优化
echo ✅ 面试全程辅导
echo.
echo ========================================
echo    💡 使用提示
echo ========================================
echo.
echo 1. 访问首页查看产品介绍
echo 2. 点击"立即使用"进入应用
echo 3. 上传简历或粘贴文本
echo 4. 等待AI协作完成
echo 5. 下载完整结果
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python web_app.py

pause

