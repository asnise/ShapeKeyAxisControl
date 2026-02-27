@echo off
echo Preparing Release...
set WORK_DIR=%TEMP%\SK_Release
set TARGET_DIR=%WORK_DIR%\ShapeKeyAxisControl
set OUT_ZIP=%~dp0..\ShapeKeyAxisControl_Release.zip

if exist "%OUT_ZIP%" del "%OUT_ZIP%"
if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"

mkdir "%TARGET_DIR%"
xcopy "%~dp0*" "%TARGET_DIR%\" /E /I /H /Y /Q

echo Cleaning up unnecessary files...
for /d /r "%TARGET_DIR%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /d /r "%TARGET_DIR%" %%d in (.git) do @if exist "%%d" rd /s /q "%%d"
del /s /q "%TARGET_DIR%\*.bat"
del /s /q "%TARGET_DIR%\*.zip"
del /s /q "%TARGET_DIR%\.gitignore"

echo Compressing Addon...
powershell -Command "Compress-Archive -Path '%TARGET_DIR%' -DestinationPath '%OUT_ZIP%' -Force"

echo Cleanup...
rmdir /s /q "%WORK_DIR%"

echo Done! Release zip created at: %OUT_ZIP%
