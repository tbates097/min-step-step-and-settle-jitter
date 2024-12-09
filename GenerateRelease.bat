@echo off
setlocal enabledelayedexpansion

set "deployment_location=K:\10. Released Software\Systems Manufacturing Support\Min Step_Step Settle_Jitter"
set "local_git_repository=C:\Users\tbates\Python\min-step-step-and-settle-jitter"
set "repository_name=Min Step_Step Settle_Jitter"

set "filelist=a1data.py InPositionJitterCollection.py MinimumIncrementalMotionCollection.py MoveAndSettleCollection.py TestInterface.py changelog.md README.md"

echo This script will overwrite all files in %deployment_location%
pause

if not exist "%deployment_location%" mkdir "%deployment_location%"

For /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set "mydate=%%c-%%a-%%b")
For /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set "mytime=%%a-%%b")

echo %username% released an update for %repository_name% at %TIME% on %DATE% >> "%deployment_location%\ReleaseLog.txt"
echo.  >> "%deployment_location%\ReleaseLog.txt"

echo Latest Commit: >> "%deployment_location%\ReleaseLog.txt"
git log -1 >> "%deployment_location%\ReleaseLog.txt"
echo.  >> "%deployment_location%\ReleaseLog.txt"

echo Tag: >> "%deployment_location%\ReleaseLog.txt"
git tag --points-at HEAD >> "%deployment_location%\ReleaseLog.txt"
echo.  >> "%deployment_location%\ReleaseLog.txt"

echo --------------------------------------------------------------------------- >> "%deployment_location%\ReleaseLog.txt"
echo.  >> "%deployment_location%\ReleaseLog.txt"

attrib +H "%deployment_location%\ReleaseLog.txt"

for %%F in (%filelist%) do (
    echo f | xcopy /y "%local_git_repository%\%%F" "%deployment_location%\%%F"
    echo "%local_git_repository%\%%F"
    echo "%deployment_location%\%%F"
)

pause
