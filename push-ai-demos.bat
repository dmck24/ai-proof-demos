@echo off
setlocal enabledelayedexpansion
title ai-proof-demos  -  PUBLIC GitHub publish/update
color 0A

REM ============================================================
REM  ONE-CLICK PUBLISH/UPDATE for the PUBLIC showcase repo
REM  dmck24/ai-proof-demos.  Double-click this file.
REM
REM  FIRST RUN: if the GitHub CLI (gh) is installed and signed in,
REM  it creates the public repo and pushes automatically. If not,
REM  it will tell you to create an EMPTY public repo named
REM  "ai-proof-demos" at https://github.com/new (owner dmck24,
REM  do NOT add a README/license), then just run this file again.
REM  Updates after that are fully automatic.
REM ============================================================

set "REPO=C:\Users\dmck2\AppData\Roaming\MetaQuotes\Terminal\Common\Files\ai-proof-demos"
set "URL=https://github.com/dmck24/ai-proof-demos.git"
set "GHD=%LOCALAPPDATA%\GitHubDesktop\GitHubDesktop.exe"

REM --- locate git: PATH, then GitHub Desktop's bundled git, then Git for Windows ---
set "GIT="
where git >nul 2>nul && set "GIT=git"
if not defined GIT for /f "delims=" %%G in ('dir /b /ad /o-n "%LOCALAPPDATA%\GitHubDesktop\app-*" 2^>nul') do (
  if not defined GIT if exist "%LOCALAPPDATA%\GitHubDesktop\%%G\resources\app\git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\GitHubDesktop\%%G\resources\app\git\cmd\git.exe"
)
if not defined GIT if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
if not defined GIT if exist "%ProgramFiles(x86)%\Git\cmd\git.exe" set "GIT=%ProgramFiles(x86)%\Git\cmd\git.exe"
if not defined GIT ( echo Could not find git. Install Git or GitHub Desktop. & pause & exit /b 1 )

cd /d "%REPO%" || ( echo Repo folder not found: %REPO% & pause & exit /b 1 )
if exist ".git\index.lock" del /f /q ".git\index.lock" >nul 2>nul

REM --- init on first run ---
if not exist ".git" (
  echo [init] Creating local git repository...
  "!GIT!" init >nul
  "!GIT!" branch -M main >nul 2>nul
)

echo [1/3] Staging changes...
"!GIT!" add -A
echo [2/3] Committing...
"!GIT!" commit -m "Publish/update ai-proof-demos %DATE% %TIME%" 2>nul

REM --- ensure a remote exists; try GitHub CLI to auto-create the repo first ---
"!GIT!" remote get-url origin >nul 2>nul
if not "!errorlevel!"=="0" (
  where gh >nul 2>nul
  if "!errorlevel!"=="0" (
    echo [remote] Creating PUBLIC repo via GitHub CLI...
    gh repo create dmck24/ai-proof-demos --public --source=. --remote=origin --push
    if "!errorlevel!"=="0" ( echo. & echo ===== PUBLISHED: %URL% ===== & echo. & pause & exit /b 0 )
  )
  echo [remote] Linking to %URL%
  "!GIT!" remote add origin "%URL%"
)

echo [3/3] Pushing to GitHub...
"!GIT!" push -u origin main
set "PUSHRC=!errorlevel!"

echo.
if "!PUSHRC!"=="0" (
  echo =====================================================
  echo   DONE  -  public repo updated:
  echo   %URL%
  echo =====================================================
) else (
  echo =====================================================
  echo   Push did not finish. If this is the FIRST run, the
  echo   GitHub repo may not exist yet.  Create an EMPTY public
  echo   repo named  ai-proof-demos  at  https://github.com/new
  echo   ^(owner dmck24, no README/license^), then run this file
  echo   again.  Opening GitHub Desktop as a fallback...
  echo =====================================================
  if exist "%GHD%" start "" "%GHD%"
)
echo.
pause
