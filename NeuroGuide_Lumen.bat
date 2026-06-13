@echo off
echo Startar NeuroGuide Lumen...
cd /d C:\NeuroGuide_Light
REM Oppna Lumen i webblasaren nar servern hunnit starta (ca 2 sek)
start "" /b cmd /c "ping -n 3 127.0.0.1 >nul & start "" http://127.0.0.1:5010/static/neuroguide_lumen.html"
REM Starta Flask-servern (Lumen anropar /berakna)
python app.py
pause
