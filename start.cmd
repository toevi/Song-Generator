@echo off
rem Song Generator: uruchamia serwer modeli (gemma), potem okno aplikacji.
cd /d "%~dp0"
python app\songgen.py %*
rem Zamkniecie okna konczy aplikacje; konsola zostaje tylko po bledzie.
if errorlevel 1 pause
