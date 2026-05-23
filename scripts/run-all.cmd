@echo off
start "GoldIdeas Backend" cmd /k "%~dp0run-backend.cmd"
start "GoldIdeas Frontend" cmd /k "%~dp0run-frontend.cmd"
echo GoldIdeas is starting.
echo Backend:  http://127.0.0.1:8765
echo Frontend: http://127.0.0.1:5180
