@echo off
chcp 65001 >nul
echo ========================================
echo 📦 准备GitHub上传文件
echo ========================================
echo.

set "source=c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"
set "target=%source%\准备上传到GitHub"

echo [1/3] 创建上传文件夹...
if exist "%target%" (
    echo 清理旧文件...
    rmdir /s /q "%target%"
)
mkdir "%target%"
echo ✅ 文件夹已创建
echo.

echo [2/3] 复制核心文件...
copy "%source%\web_app.py" "%target%\" >nul
copy "%source%\requirements.txt" "%target%\" >nul
copy "%source%\Procfile" "%target%\" >nul
copy "%source%\render.yaml" "%target%\" >nul
copy "%source%\runtime.txt" "%target%\" >nul
copy "%source%\README.md" "%target%\" >nul
echo ✅ 核心文件已复制
echo.

echo [3/3] 复制文件夹...
xcopy "%source%\app" "%target%\app\" /E /I /Y >nul
xcopy "%source%\static" "%target%\static\" /E /I /Y >nul
xcopy "%source%\data" "%target%\data\" /E /I /Y >nul
echo ✅ 文件夹已复制
echo.

echo ========================================
echo ✅ 准备完成！
echo ========================================
echo.
echo 📁 上传文件夹位置：
echo    %target%
echo.
echo 📋 下一步：
echo    1. 打开上面的文件夹
echo    2. 全选里面的所有文件（Ctrl+A）
echo    3. 访问 https://github.com/emptyteabot/ai-job-helper
echo    4. 点击 Add file → Upload files
echo    5. 拖拽所有文件到网页
echo    6. 点击 Commit changes
echo.
echo 💡 提示：如果GitHub上有旧文件，先删除再上传
echo.

explorer "%target%"

pause

chcp 65001 >nul
echo ========================================
echo 📦 准备GitHub上传文件
echo ========================================
echo.

set "source=c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"
set "target=%source%\准备上传到GitHub"

echo [1/3] 创建上传文件夹...
if exist "%target%" (
    echo 清理旧文件...
    rmdir /s /q "%target%"
)
mkdir "%target%"
echo ✅ 文件夹已创建
echo.

echo [2/3] 复制核心文件...
copy "%source%\web_app.py" "%target%\" >nul
copy "%source%\requirements.txt" "%target%\" >nul
copy "%source%\Procfile" "%target%\" >nul
copy "%source%\render.yaml" "%target%\" >nul
copy "%source%\runtime.txt" "%target%\" >nul
copy "%source%\README.md" "%target%\" >nul
echo ✅ 核心文件已复制
echo.

echo [3/3] 复制文件夹...
xcopy "%source%\app" "%target%\app\" /E /I /Y >nul
xcopy "%source%\static" "%target%\static\" /E /I /Y >nul
xcopy "%source%\data" "%target%\data\" /E /I /Y >nul
echo ✅ 文件夹已复制
echo.

echo ========================================
echo ✅ 准备完成！
echo ========================================
echo.
echo 📁 上传文件夹位置：
echo    %target%
echo.
echo 📋 下一步：
echo    1. 打开上面的文件夹
echo    2. 全选里面的所有文件（Ctrl+A）
echo    3. 访问 https://github.com/emptyteabot/ai-job-helper
echo    4. 点击 Add file → Upload files
echo    5. 拖拽所有文件到网页
echo    6. 点击 Commit changes
echo.
echo 💡 提示：如果GitHub上有旧文件，先删除再上传
echo.

explorer "%target%"

pause

chcp 65001 >nul
echo ========================================
echo 📦 准备GitHub上传文件
echo ========================================
echo.

set "source=c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"
set "target=%source%\准备上传到GitHub"

echo [1/3] 创建上传文件夹...
if exist "%target%" (
    echo 清理旧文件...
    rmdir /s /q "%target%"
)
mkdir "%target%"
echo ✅ 文件夹已创建
echo.

echo [2/3] 复制核心文件...
copy "%source%\web_app.py" "%target%\" >nul
copy "%source%\requirements.txt" "%target%\" >nul
copy "%source%\Procfile" "%target%\" >nul
copy "%source%\render.yaml" "%target%\" >nul
copy "%source%\runtime.txt" "%target%\" >nul
copy "%source%\README.md" "%target%\" >nul
echo ✅ 核心文件已复制
echo.

echo [3/3] 复制文件夹...
xcopy "%source%\app" "%target%\app\" /E /I /Y >nul
xcopy "%source%\static" "%target%\static\" /E /I /Y >nul
xcopy "%source%\data" "%target%\data\" /E /I /Y >nul
echo ✅ 文件夹已复制
echo.

echo ========================================
echo ✅ 准备完成！
echo ========================================
echo.
echo 📁 上传文件夹位置：
echo    %target%
echo.
echo 📋 下一步：
echo    1. 打开上面的文件夹
echo    2. 全选里面的所有文件（Ctrl+A）
echo    3. 访问 https://github.com/emptyteabot/ai-job-helper
echo    4. 点击 Add file → Upload files
echo    5. 拖拽所有文件到网页
echo    6. 点击 Commit changes
echo.
echo 💡 提示：如果GitHub上有旧文件，先删除再上传
echo.

explorer "%target%"

pause

chcp 65001 >nul
echo ========================================
echo 📦 准备GitHub上传文件
echo ========================================
echo.

set "source=c:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"
set "target=%source%\准备上传到GitHub"

echo [1/3] 创建上传文件夹...
if exist "%target%" (
    echo 清理旧文件...
    rmdir /s /q "%target%"
)
mkdir "%target%"
echo ✅ 文件夹已创建
echo.

echo [2/3] 复制核心文件...
copy "%source%\web_app.py" "%target%\" >nul
copy "%source%\requirements.txt" "%target%\" >nul
copy "%source%\Procfile" "%target%\" >nul
copy "%source%\render.yaml" "%target%\" >nul
copy "%source%\runtime.txt" "%target%\" >nul
copy "%source%\README.md" "%target%\" >nul
echo ✅ 核心文件已复制
echo.

echo [3/3] 复制文件夹...
xcopy "%source%\app" "%target%\app\" /E /I /Y >nul
xcopy "%source%\static" "%target%\static\" /E /I /Y >nul
xcopy "%source%\data" "%target%\data\" /E /I /Y >nul
echo ✅ 文件夹已复制
echo.

echo ========================================
echo ✅ 准备完成！
echo ========================================
echo.
echo 📁 上传文件夹位置：
echo    %target%
echo.
echo 📋 下一步：
echo    1. 打开上面的文件夹
echo    2. 全选里面的所有文件（Ctrl+A）
echo    3. 访问 https://github.com/emptyteabot/ai-job-helper
echo    4. 点击 Add file → Upload files
echo    5. 拖拽所有文件到网页
echo    6. 点击 Commit changes
echo.
echo 💡 提示：如果GitHub上有旧文件，先删除再上传
echo.

explorer "%target%"

pause



