@echo off
setlocal
cd /d "%~dp0"

echo ===============================================
echo Dota 2 Asset Studio - Windows Build
echo ===============================================

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

python -m pytest -q
if errorlevel 1 (
  echo Tests failed. Build cancelled.
  exit /b 1
)

python -m PyInstaller --noconfirm --clean --onefile --windowed --name Dota2AssetStudio --icon=assets\Dota2AssetStudio.ico main.py
if errorlevel 1 exit /b 1

copy /Y heroes.txt dist\heroes.txt >nul
copy /Y neutral_creeps.txt dist\neutral_creeps.txt >nul
copy /Y items.txt dist\items.txt >nul
copy /Y README.txt dist\README.txt >nul

if not exist dist\output mkdir dist\output
if not exist dist\cache mkdir dist\cache

echo.
echo ===============================================
echo BUILT SUCCESSFULLY:
echo %CD%\dist\Dota2AssetStudio.exe
echo ===============================================
endlocal
