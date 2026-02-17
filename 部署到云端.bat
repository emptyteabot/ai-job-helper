@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 云端部署准备工具
echo ========================================
echo.

echo [1/5] 检查部署文件...
set missing=0

if not exist requirements.txt (
    echo ❌ requirements.txt 缺失
    set missing=1
) else (
    echo ✅ requirements.txt
)

if not exist web_app.py (
    echo ❌ web_app.py 缺失
    set missing=1
) else (
    echo ✅ web_app.py
)

if not exist Procfile (
    echo ❌ Procfile 缺失
    set missing=1
) else (
    echo ✅ Procfile
)

if not exist railway.json (
    echo ❌ railway.json 缺失
    set missing=1
) else (
    echo ✅ railway.json
)

if %missing%==1 (
    echo.
    echo ❌ 缺少必要文件，无法部署
    pause
    exit /b 1
)
echo.

echo [2/5] 检查Railway CLI...
where railway >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Railway CLI 未安装
    echo.
    echo 📦 安装方法：
    echo   npm install -g @railway/cli
    echo.
    echo 或者访问：https://docs.railway.app/develop/cli
    echo.
    set /p install="是否现在安装？(需要npm) (y/n): "
    if /i "%install%"=="y" (
        npm install -g @railway/cli
        if errorlevel 1 (
            echo ❌ 安装失败
            pause
            exit /b 1
        )
        echo ✅ 安装成功
    ) else (
        echo 请手动安装后重试
        pause
        exit /b 1
    )
) else (
    echo ✅ Railway CLI 已安装
    railway --version
)
echo.

echo [3/5] 生成API密钥...
echo.
echo 🔑 正在生成安全的API密钥...
python -c "import secrets; print('CRAWLER_API_KEY=' + secrets.token_urlsafe(32))" > temp_key.txt
type temp_key.txt
echo.
echo ⚠️ 请保存上面的密钥，稍后配置时需要用到
echo.
pause
echo.

echo [4/5] 准备环境变量...
echo.
echo 📝 请准备以下信息：
echo.
echo 1. DeepSeek API Key
echo    获取地址: https://platform.deepseek.com/api_keys
echo.
set /p deepseek_key="请输入您的 DeepSeek API Key: "
echo.

echo 2. 爬虫API密钥（刚才生成的）
set /p crawler_key="请输入刚才生成的 CRAWLER_API_KEY: "
echo.

echo [5/5] 开始部署...
echo.
echo 📋 部署选项：
echo   1. Railway（推荐）
echo   2. Render（需要GitHub）
echo   3. 手动部署
echo.
set /p choice="请选择 (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 开始 Railway 部署...
    echo.
    
    echo 步骤1: 登录Railway
    railway login
    if errorlevel 1 (
        echo ❌ 登录失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤2: 初始化项目
    railway init
    if errorlevel 1 (
        echo ❌ 初始化失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤3: 设置环境变量
    railway variables set DEEPSEEK_API_KEY=%deepseek_key%
    railway variables set CRAWLER_API_KEY=%crawler_key%
    railway variables set JOB_DATA_PROVIDER=cloud
    railway variables set PORT=8000
    echo.
    
    echo 步骤4: 部署
    railway up
    if errorlevel 1 (
        echo ❌ 部署失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤5: 生成域名
    railway domain
    echo.
    
    echo ========================================
    echo ✅ 部署完成！
    echo ========================================
    echo.
    echo 📝 请记录以下信息：
    echo.
    echo 1. 云端URL（上面显示的域名）
    echo    https://_____________________.railway.app
    echo.
    echo 2. 爬虫API密钥
    type temp_key.txt
    echo.
    echo 💡 下一步：
    echo   1. 访问您的云端URL测试
    echo   2. 配置本地爬虫（编辑 crawler.env）
    echo   3. 启动爬虫服务
    echo.
    
) else if "%choice%"=="2" (
    echo.
    echo 📖 Render 部署步骤：
    echo.
    echo 1. 创建GitHub仓库
    echo    git init
    echo    git add .
    echo    git commit -m "Initial commit"
    echo    git remote add origin https://github.com/你的用户名/ai-job-helper.git
    echo    git push -u origin main
    echo.
    echo 2. 访问 https://render.com
    echo    - 使用GitHub登录
    echo    - 创建新的Web Service
    echo    - 选择您的仓库
    echo.
    echo 3. 配置环境变量：
    echo    DEEPSEEK_API_KEY = %deepseek_key%
    type temp_key.txt
    echo    JOB_DATA_PROVIDER = cloud
    echo    PORT = 8000
    echo.
    echo 4. 点击 "Create Web Service"
    echo.
    
) else (
    echo.
    echo 📖 手动部署说明：
    echo.
    echo 请查看详细文档：
    echo   docs\云端部署步骤.md
    echo.
)

del temp_key.txt 2>nul

echo.
pause

chcp 65001 >nul
echo ========================================
echo 🚀 云端部署准备工具
echo ========================================
echo.

echo [1/5] 检查部署文件...
set missing=0

if not exist requirements.txt (
    echo ❌ requirements.txt 缺失
    set missing=1
) else (
    echo ✅ requirements.txt
)

if not exist web_app.py (
    echo ❌ web_app.py 缺失
    set missing=1
) else (
    echo ✅ web_app.py
)

if not exist Procfile (
    echo ❌ Procfile 缺失
    set missing=1
) else (
    echo ✅ Procfile
)

if not exist railway.json (
    echo ❌ railway.json 缺失
    set missing=1
) else (
    echo ✅ railway.json
)

if %missing%==1 (
    echo.
    echo ❌ 缺少必要文件，无法部署
    pause
    exit /b 1
)
echo.

echo [2/5] 检查Railway CLI...
where railway >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Railway CLI 未安装
    echo.
    echo 📦 安装方法：
    echo   npm install -g @railway/cli
    echo.
    echo 或者访问：https://docs.railway.app/develop/cli
    echo.
    set /p install="是否现在安装？(需要npm) (y/n): "
    if /i "%install%"=="y" (
        npm install -g @railway/cli
        if errorlevel 1 (
            echo ❌ 安装失败
            pause
            exit /b 1
        )
        echo ✅ 安装成功
    ) else (
        echo 请手动安装后重试
        pause
        exit /b 1
    )
) else (
    echo ✅ Railway CLI 已安装
    railway --version
)
echo.

echo [3/5] 生成API密钥...
echo.
echo 🔑 正在生成安全的API密钥...
python -c "import secrets; print('CRAWLER_API_KEY=' + secrets.token_urlsafe(32))" > temp_key.txt
type temp_key.txt
echo.
echo ⚠️ 请保存上面的密钥，稍后配置时需要用到
echo.
pause
echo.

echo [4/5] 准备环境变量...
echo.
echo 📝 请准备以下信息：
echo.
echo 1. DeepSeek API Key
echo    获取地址: https://platform.deepseek.com/api_keys
echo.
set /p deepseek_key="请输入您的 DeepSeek API Key: "
echo.

echo 2. 爬虫API密钥（刚才生成的）
set /p crawler_key="请输入刚才生成的 CRAWLER_API_KEY: "
echo.

echo [5/5] 开始部署...
echo.
echo 📋 部署选项：
echo   1. Railway（推荐）
echo   2. Render（需要GitHub）
echo   3. 手动部署
echo.
set /p choice="请选择 (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 开始 Railway 部署...
    echo.
    
    echo 步骤1: 登录Railway
    railway login
    if errorlevel 1 (
        echo ❌ 登录失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤2: 初始化项目
    railway init
    if errorlevel 1 (
        echo ❌ 初始化失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤3: 设置环境变量
    railway variables set DEEPSEEK_API_KEY=%deepseek_key%
    railway variables set CRAWLER_API_KEY=%crawler_key%
    railway variables set JOB_DATA_PROVIDER=cloud
    railway variables set PORT=8000
    echo.
    
    echo 步骤4: 部署
    railway up
    if errorlevel 1 (
        echo ❌ 部署失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤5: 生成域名
    railway domain
    echo.
    
    echo ========================================
    echo ✅ 部署完成！
    echo ========================================
    echo.
    echo 📝 请记录以下信息：
    echo.
    echo 1. 云端URL（上面显示的域名）
    echo    https://_____________________.railway.app
    echo.
    echo 2. 爬虫API密钥
    type temp_key.txt
    echo.
    echo 💡 下一步：
    echo   1. 访问您的云端URL测试
    echo   2. 配置本地爬虫（编辑 crawler.env）
    echo   3. 启动爬虫服务
    echo.
    
) else if "%choice%"=="2" (
    echo.
    echo 📖 Render 部署步骤：
    echo.
    echo 1. 创建GitHub仓库
    echo    git init
    echo    git add .
    echo    git commit -m "Initial commit"
    echo    git remote add origin https://github.com/你的用户名/ai-job-helper.git
    echo    git push -u origin main
    echo.
    echo 2. 访问 https://render.com
    echo    - 使用GitHub登录
    echo    - 创建新的Web Service
    echo    - 选择您的仓库
    echo.
    echo 3. 配置环境变量：
    echo    DEEPSEEK_API_KEY = %deepseek_key%
    type temp_key.txt
    echo    JOB_DATA_PROVIDER = cloud
    echo    PORT = 8000
    echo.
    echo 4. 点击 "Create Web Service"
    echo.
    
) else (
    echo.
    echo 📖 手动部署说明：
    echo.
    echo 请查看详细文档：
    echo   docs\云端部署步骤.md
    echo.
)

del temp_key.txt 2>nul

echo.
pause

chcp 65001 >nul
echo ========================================
echo 🚀 云端部署准备工具
echo ========================================
echo.

echo [1/5] 检查部署文件...
set missing=0

if not exist requirements.txt (
    echo ❌ requirements.txt 缺失
    set missing=1
) else (
    echo ✅ requirements.txt
)

if not exist web_app.py (
    echo ❌ web_app.py 缺失
    set missing=1
) else (
    echo ✅ web_app.py
)

if not exist Procfile (
    echo ❌ Procfile 缺失
    set missing=1
) else (
    echo ✅ Procfile
)

if not exist railway.json (
    echo ❌ railway.json 缺失
    set missing=1
) else (
    echo ✅ railway.json
)

if %missing%==1 (
    echo.
    echo ❌ 缺少必要文件，无法部署
    pause
    exit /b 1
)
echo.

echo [2/5] 检查Railway CLI...
where railway >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Railway CLI 未安装
    echo.
    echo 📦 安装方法：
    echo   npm install -g @railway/cli
    echo.
    echo 或者访问：https://docs.railway.app/develop/cli
    echo.
    set /p install="是否现在安装？(需要npm) (y/n): "
    if /i "%install%"=="y" (
        npm install -g @railway/cli
        if errorlevel 1 (
            echo ❌ 安装失败
            pause
            exit /b 1
        )
        echo ✅ 安装成功
    ) else (
        echo 请手动安装后重试
        pause
        exit /b 1
    )
) else (
    echo ✅ Railway CLI 已安装
    railway --version
)
echo.

echo [3/5] 生成API密钥...
echo.
echo 🔑 正在生成安全的API密钥...
python -c "import secrets; print('CRAWLER_API_KEY=' + secrets.token_urlsafe(32))" > temp_key.txt
type temp_key.txt
echo.
echo ⚠️ 请保存上面的密钥，稍后配置时需要用到
echo.
pause
echo.

echo [4/5] 准备环境变量...
echo.
echo 📝 请准备以下信息：
echo.
echo 1. DeepSeek API Key
echo    获取地址: https://platform.deepseek.com/api_keys
echo.
set /p deepseek_key="请输入您的 DeepSeek API Key: "
echo.

echo 2. 爬虫API密钥（刚才生成的）
set /p crawler_key="请输入刚才生成的 CRAWLER_API_KEY: "
echo.

echo [5/5] 开始部署...
echo.
echo 📋 部署选项：
echo   1. Railway（推荐）
echo   2. Render（需要GitHub）
echo   3. 手动部署
echo.
set /p choice="请选择 (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 开始 Railway 部署...
    echo.
    
    echo 步骤1: 登录Railway
    railway login
    if errorlevel 1 (
        echo ❌ 登录失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤2: 初始化项目
    railway init
    if errorlevel 1 (
        echo ❌ 初始化失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤3: 设置环境变量
    railway variables set DEEPSEEK_API_KEY=%deepseek_key%
    railway variables set CRAWLER_API_KEY=%crawler_key%
    railway variables set JOB_DATA_PROVIDER=cloud
    railway variables set PORT=8000
    echo.
    
    echo 步骤4: 部署
    railway up
    if errorlevel 1 (
        echo ❌ 部署失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤5: 生成域名
    railway domain
    echo.
    
    echo ========================================
    echo ✅ 部署完成！
    echo ========================================
    echo.
    echo 📝 请记录以下信息：
    echo.
    echo 1. 云端URL（上面显示的域名）
    echo    https://_____________________.railway.app
    echo.
    echo 2. 爬虫API密钥
    type temp_key.txt
    echo.
    echo 💡 下一步：
    echo   1. 访问您的云端URL测试
    echo   2. 配置本地爬虫（编辑 crawler.env）
    echo   3. 启动爬虫服务
    echo.
    
) else if "%choice%"=="2" (
    echo.
    echo 📖 Render 部署步骤：
    echo.
    echo 1. 创建GitHub仓库
    echo    git init
    echo    git add .
    echo    git commit -m "Initial commit"
    echo    git remote add origin https://github.com/你的用户名/ai-job-helper.git
    echo    git push -u origin main
    echo.
    echo 2. 访问 https://render.com
    echo    - 使用GitHub登录
    echo    - 创建新的Web Service
    echo    - 选择您的仓库
    echo.
    echo 3. 配置环境变量：
    echo    DEEPSEEK_API_KEY = %deepseek_key%
    type temp_key.txt
    echo    JOB_DATA_PROVIDER = cloud
    echo    PORT = 8000
    echo.
    echo 4. 点击 "Create Web Service"
    echo.
    
) else (
    echo.
    echo 📖 手动部署说明：
    echo.
    echo 请查看详细文档：
    echo   docs\云端部署步骤.md
    echo.
)

del temp_key.txt 2>nul

echo.
pause

chcp 65001 >nul
echo ========================================
echo 🚀 云端部署准备工具
echo ========================================
echo.

echo [1/5] 检查部署文件...
set missing=0

if not exist requirements.txt (
    echo ❌ requirements.txt 缺失
    set missing=1
) else (
    echo ✅ requirements.txt
)

if not exist web_app.py (
    echo ❌ web_app.py 缺失
    set missing=1
) else (
    echo ✅ web_app.py
)

if not exist Procfile (
    echo ❌ Procfile 缺失
    set missing=1
) else (
    echo ✅ Procfile
)

if not exist railway.json (
    echo ❌ railway.json 缺失
    set missing=1
) else (
    echo ✅ railway.json
)

if %missing%==1 (
    echo.
    echo ❌ 缺少必要文件，无法部署
    pause
    exit /b 1
)
echo.

echo [2/5] 检查Railway CLI...
where railway >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Railway CLI 未安装
    echo.
    echo 📦 安装方法：
    echo   npm install -g @railway/cli
    echo.
    echo 或者访问：https://docs.railway.app/develop/cli
    echo.
    set /p install="是否现在安装？(需要npm) (y/n): "
    if /i "%install%"=="y" (
        npm install -g @railway/cli
        if errorlevel 1 (
            echo ❌ 安装失败
            pause
            exit /b 1
        )
        echo ✅ 安装成功
    ) else (
        echo 请手动安装后重试
        pause
        exit /b 1
    )
) else (
    echo ✅ Railway CLI 已安装
    railway --version
)
echo.

echo [3/5] 生成API密钥...
echo.
echo 🔑 正在生成安全的API密钥...
python -c "import secrets; print('CRAWLER_API_KEY=' + secrets.token_urlsafe(32))" > temp_key.txt
type temp_key.txt
echo.
echo ⚠️ 请保存上面的密钥，稍后配置时需要用到
echo.
pause
echo.

echo [4/5] 准备环境变量...
echo.
echo 📝 请准备以下信息：
echo.
echo 1. DeepSeek API Key
echo    获取地址: https://platform.deepseek.com/api_keys
echo.
set /p deepseek_key="请输入您的 DeepSeek API Key: "
echo.

echo 2. 爬虫API密钥（刚才生成的）
set /p crawler_key="请输入刚才生成的 CRAWLER_API_KEY: "
echo.

echo [5/5] 开始部署...
echo.
echo 📋 部署选项：
echo   1. Railway（推荐）
echo   2. Render（需要GitHub）
echo   3. 手动部署
echo.
set /p choice="请选择 (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 🚀 开始 Railway 部署...
    echo.
    
    echo 步骤1: 登录Railway
    railway login
    if errorlevel 1 (
        echo ❌ 登录失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤2: 初始化项目
    railway init
    if errorlevel 1 (
        echo ❌ 初始化失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤3: 设置环境变量
    railway variables set DEEPSEEK_API_KEY=%deepseek_key%
    railway variables set CRAWLER_API_KEY=%crawler_key%
    railway variables set JOB_DATA_PROVIDER=cloud
    railway variables set PORT=8000
    echo.
    
    echo 步骤4: 部署
    railway up
    if errorlevel 1 (
        echo ❌ 部署失败
        pause
        exit /b 1
    )
    echo.
    
    echo 步骤5: 生成域名
    railway domain
    echo.
    
    echo ========================================
    echo ✅ 部署完成！
    echo ========================================
    echo.
    echo 📝 请记录以下信息：
    echo.
    echo 1. 云端URL（上面显示的域名）
    echo    https://_____________________.railway.app
    echo.
    echo 2. 爬虫API密钥
    type temp_key.txt
    echo.
    echo 💡 下一步：
    echo   1. 访问您的云端URL测试
    echo   2. 配置本地爬虫（编辑 crawler.env）
    echo   3. 启动爬虫服务
    echo.
    
) else if "%choice%"=="2" (
    echo.
    echo 📖 Render 部署步骤：
    echo.
    echo 1. 创建GitHub仓库
    echo    git init
    echo    git add .
    echo    git commit -m "Initial commit"
    echo    git remote add origin https://github.com/你的用户名/ai-job-helper.git
    echo    git push -u origin main
    echo.
    echo 2. 访问 https://render.com
    echo    - 使用GitHub登录
    echo    - 创建新的Web Service
    echo    - 选择您的仓库
    echo.
    echo 3. 配置环境变量：
    echo    DEEPSEEK_API_KEY = %deepseek_key%
    type temp_key.txt
    echo    JOB_DATA_PROVIDER = cloud
    echo    PORT = 8000
    echo.
    echo 4. 点击 "Create Web Service"
    echo.
    
) else (
    echo.
    echo 📖 手动部署说明：
    echo.
    echo 请查看详细文档：
    echo   docs\云端部署步骤.md
    echo.
)

del temp_key.txt 2>nul

echo.
pause



