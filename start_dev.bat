@echo off
rem ============================================================
rem 校园失物招领平台 - 开发环境一键启动
rem 双击运行：同时启动 Flask 后端(5000) 与 Vite 前端(5173)
rem 访问入口：http://127.0.0.1:5173
rem 关闭：直接关掉弹出的两个命令行窗口
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"

echo [1/2] 启动后端 Flask (http://127.0.0.1:5000) ...
start "lostfound-backend" cmd /k "cd server && .venv\Scripts\python.exe run.py"

echo [2/2] 启动前端 Vite  (http://127.0.0.1:5173) ...
start "lostfound-web" cmd /k "cd web && npm run dev"

echo.
echo 两个窗口已启动。等待约 5 秒后访问：http://127.0.0.1:5173
echo （如果前端窗口提示 Port 5173 is in use，说明前端已在运行，直接用现有页面即可）
