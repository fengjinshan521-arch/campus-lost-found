@echo off
REM 校园失物招领信息平台 —— Windows 生产启动脚本（waitress）
REM 用法：双击运行，或用 NSSM 注册为服务：nssm install LostFound deploy\start_waitress.bat

setlocal
cd /d "%~dp0..\server"

set FLASK_ENV=production
set FLASK_APP=run:app

if not exist ".venv\Scripts\waitress-serve.exe" (
    echo 正在安装 waitress ...
    .venv\Scripts\python.exe -m pip install waitress
)

echo 启动服务： http://0.0.0.0:5000
.venv\Scripts\waitress-serve.exe --host 0.0.0.0 --port 5000 --threads 8 run:app

endlocal
