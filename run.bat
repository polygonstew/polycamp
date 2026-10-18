@echo off
rem Start Polycamp on the LAN (default port 8570). Needs only Python 3.8+ (py launcher or python on PATH).
cd /d "%~dp0"
where py >nul 2>nul && (py -3 server\polycamp.py %*) || (python server\polycamp.py %*)
