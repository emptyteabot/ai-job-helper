@echo off
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     真实招聘数据 - 测试启动            ║
echo ╚════════════════════════════════════════╝
echo.

echo [1/3] 测试真实招聘数据服务...
python -c "from app.services.real_job_service import RealJobService; s = RealJobService(); stats = s.get_statistics(); print(f'\n✅ 数据库加载成功!\n总岗位数: {stats[\"total_jobs\"]}\n总公司数: {stats[\"total_companies\"]}\n平台分布: {stats[\"platforms\"]}')"

if errorlevel 1 (
    echo.
    echo ❌ 数据服务测试失败
    pause
    exit /b 1
)

echo.
echo [2/3] 设置API密钥...
set DEEPSEEK_API_KEY=sk-da34a79604824fc28f73fca8381ed92f

echo.
echo [3/3] 启动服务...
echo.
echo ╔════════════════════════════════════════╗
echo ║  🎉 真实招聘数据已加载！               ║
echo ║                                        ║
echo ║  📊 数据统计:                          ║
echo ║     - 1000+ 真实岗位                   ║
echo ║     - 60+ 知名公司                     ║
echo ║     - 4大招聘平台                      ║
echo ║                                        ║
echo ║  📍 http://localhost:8000              ║
echo ║                                        ║
echo ║  💡 新功能:                            ║
echo ║     ✓ 真实岗位搜索                     ║
echo ║     ✓ 智能匹配推荐                     ║
echo ║     ✓ 一键批量投递                     ║
echo ║     ✓ 投递记录跟踪                     ║
echo ║                                        ║
echo ╚════════════════════════════════════════╝
echo.

timeout /t 2 >nul
start http://localhost:8000

python web_app.py

pause

