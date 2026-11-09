@echo off
chcp 65001 >nul
title 🕷️ 蜘蛛感應 - 每日財金新聞戰情室
echo ========================================================
echo   🕷️ 正在清理舊進程並啟動 蜘蛛感應 戰情室...
echo ========================================================
echo.

:: 關閉可能在背景殘留佔用 8080 端口的舊 Python 程序
taskkill /F /IM python.exe /T 2>nul

cd /d "%~dp0"

echo.
echo [提示] 正在為您開啟瀏覽器：http://localhost:8080
echo [提示] 若畫面有舊快取，請在瀏覽器按下 Ctrl + F5 強制重整！
echo.

start http://localhost:8080

"C:\Users\1013i\AppData\Local\Programs\Python\Python314\python.exe" server.py
pause
