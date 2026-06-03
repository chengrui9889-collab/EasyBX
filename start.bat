@echo off
chcp 65001 >nul
title EasyBX - 智能发票报销管理助手

echo ========================================
echo   EasyBX - 一键启动
echo ========================================
echo.

:: 检查 .env 文件
if not exist ".env" (
    echo [警告] .env 文件不存在, 正在从 .env.example 复制...
    copy .env.example .env >nul
    echo [提示] 请编辑 .env 文件后重新启动
    pause
    exit /b 1
)

:: 启动后端 (端口 0220)
echo [1/2] 启动后端服务 (端口 0220)...
start "EasyBX-Server" cmd /c "cd /d %~dp0server && python -m uvicorn main:app --host 0.0.0.0 --port 0220 --reload"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端 (端口 5173)
echo [2/2] 启动前端开发服务器 (端口 5173)...
start "EasyBX-Web" cmd /c "cd /d %~dp0web && npm run dev"

echo.
echo ========================================
echo   EasyBX 启动完成!
echo   后端: http://localhost:0220
echo   API文档: http://localhost:0220/docs
echo   前端: http://localhost:5180
echo ========================================
echo.
echo 关闭此窗口不会停止服务.
echo 请分别关闭 "EasyBX-Server" 和 "EasyBX-Web" 窗口来停止服务.
pause
