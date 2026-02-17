@echo off
chcp 65001 >nul
echo ========================================
echo 自动投递测试套件
echo ========================================
echo.

:menu
echo 请选择测试类型:
echo [1] 运行所有测试
echo [2] 运行 Boss直聘测试
echo [3] 运行智联招聘测试
echo [4] 运行多平台集成测试
echo [5] 运行单元测试
echo [6] 运行集成测试
echo [7] 生成覆盖率报告
echo [8] 运行性能测试
echo [0] 退出
echo.

set /p choice="请输入选项 (0-8): "

if "%choice%"=="1" goto all_tests
if "%choice%"=="2" goto boss_tests
if "%choice%"=="3" goto zhilian_tests
if "%choice%"=="4" goto multi_tests
if "%choice%"=="5" goto unit_tests
if "%choice%"=="6" goto integration_tests
if "%choice%"=="7" goto coverage
if "%choice%"=="8" goto performance
if "%choice%"=="0" goto end

echo 无效选项，请重新选择
goto menu

:all_tests
echo.
echo 运行所有测试...
pytest tests/ -v
goto end_test

:boss_tests
echo.
echo 运行 Boss直聘测试...
pytest tests/test_boss_applier.py -v
goto end_test

:zhilian_tests
echo.
echo 运行智联招聘测试...
pytest tests/test_zhilian_applier.py -v
goto end_test

:multi_tests
echo.
echo 运行多平台集成测试...
pytest tests/test_multi_platform.py -v
goto end_test

:unit_tests
echo.
echo 运行单元测试...
pytest tests/ -v -m unit
goto end_test

:integration_tests
echo.
echo 运行集成测试...
pytest tests/ -v -m integration
goto end_test

:coverage
echo.
echo 生成覆盖率报告...
pytest tests/ --cov=app --cov-report=html --cov-report=term
echo.
echo 覆盖率报告已生成到 htmlcov/index.html
start htmlcov\index.html
goto end_test

:performance
echo.
echo 运行性能测试...
pytest tests/ -v -m performance
goto end_test

:end_test
echo.
echo ========================================
echo 测试完成
echo ========================================
pause
goto menu

:end
echo.
echo 再见！
exit /b 0
