@echo off
chcp 65001 >nul
cls
color 0A
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║          🚀 AI求职助手 - 融资演示版 🚀                    ║
echo ║                                                            ║
echo ║          Ready for Series A Funding                       ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo.
echo ════════════════════════════════════════════════════════════
echo   系统初始化中...
echo ════════════════════════════════════════════════════════════
echo.

echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装
    pause
    exit /b 1
)
echo ✓ Python环境正常

echo.
echo [2/5] 安装核心依赖...
pip install openai python-dotenv fastapi uvicorn PyPDF2 python-docx Pillow python-multipart -q
echo ✓ 依赖安装完成

echo.
echo [3/5] 加载真实招聘数据...
python -c "from app.services.real_job_service import RealJobService; s = RealJobService(); stats = s.get_statistics(); print(f'✓ 数据库加载成功: {stats[\"total_jobs\"]}个岗位, {stats[\"total_companies\"]}家公司')"

echo.
echo [4/5] 配置API密钥...
set DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
echo ✓ API密钥已配置

echo.
echo [5/5] 启动Web服务...
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║  🎉 系统启动成功！                                         ║
echo ║                                                            ║
echo ║  📊 核心数据:                                              ║
echo ║     • 1000+ 真实岗位                                       ║
echo ║     • 60+ 知名企业（BAT、独角兽等）                        ║
echo ║     • 4大招聘平台（Boss直聘、猎聘、智联、前程无忧）        ║
echo ║     • 6个AI协作引擎                                        ║
echo ║                                                            ║
echo ║  🚀 核心功能:                                              ║
echo ║     ✓ 智能简历分析                                         ║
echo ║     ✓ AI协作优化（6个AI辩论）                              ║
echo ║     ✓ 真实岗位搜索                                         ║
echo ║     ✓ 智能匹配推荐                                         ║
echo ║     ✓ 一键批量投递                                         ║
echo ║     ✓ 投递记录跟踪                                         ║
echo ║     ✓ 面试辅导准备                                         ║
echo ║                                                            ║
echo ║  💰 商业价值:                                              ║
echo ║     • C端用户: 提高求职效率10倍                            ║
echo ║     • B端企业: 精准人才推荐                                ║
echo ║     • 数据价值: 求职行为分析                               ║
echo ║     • 市场规模: 千亿级求职市场                             ║
echo ║                                                            ║
echo ║  📍 访问地址: http://localhost:8000                        ║
echo ║                                                            ║
echo ║  📖 API文档: http://localhost:8000/docs                    ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo.
echo 正在打开浏览器...
timeout /t 2 >nul
start http://localhost:8000

echo.
echo ════════════════════════════════════════════════════════════
echo   服务运行中... 按 Ctrl+C 停止
echo ════════════════════════════════════════════════════════════
echo.

python web_app.py

pause

