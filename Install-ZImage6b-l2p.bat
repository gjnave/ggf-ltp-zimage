@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO_URL=https://github.com/gjnave/ggf-ltp-zimage.git"
set "NODE_NAME=ggf-ltp-zimage"
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "FORCE=0"
set "COMFY_ROOT="
set "SCRIPT_IS_REPO=0"

title Install ZImage6b L2P for ComfyUI

if /I "%~1"=="help" goto :help
if /I "%~1"=="/?" goto :help
if /I "%~1"=="-h" goto :help
if /I "%~1"=="--help" goto :help

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="--force" (
    set "FORCE=1"
    shift
    goto :parse_args
)
if /I "%~1"=="/force" (
    set "FORCE=1"
    shift
    goto :parse_args
)
if not defined COMFY_ROOT (
    set "COMFY_ROOT=%~1"
)
shift
goto :parse_args

:args_done
echo.
echo Install-ZImage6b-l2p.bat
echo %REPO_URL%
echo.

call :resolve_comfy_root
if errorlevel 1 exit /b 1

call :find_python
if errorlevel 1 exit /b 1

echo ComfyUI root: "%COMFY_ROOT%"
echo ComfyUI Python: "%COMFY_PYTHON%"
echo.

call :activate_python
call :install_node
if errorlevel 1 exit /b 1

call :download_models
if errorlevel 1 exit /b 1

echo.
echo Done.
echo Restart ComfyUI, then load workflows\ggf_l2p_zimage_6b_no_vae.json from the custom node folder.
exit /b 0

:help
echo.
echo Install-ZImage6b-l2p.bat
echo.
echo Installs the ggf-ltp-zimage ComfyUI custom node and downloads required model files.
echo.
echo Usage:
echo   Install-ZImage6b-l2p.bat C:\path\to\ComfyUI
echo.
echo Portable example:
echo   Install-ZImage6b-l2p.bat C:\ComfyUI_windows_portable\ComfyUI
echo.
echo Options:
echo   --force    Re-download model files even if they already exist
echo.
exit /b 0

:resolve_comfy_root
if defined COMFY_ROOT (
    call :check_root "%COMFY_ROOT%"
    if not errorlevel 1 exit /b 0
)

call :check_root "%CD%"
if not errorlevel 1 exit /b 0

call :check_root "%CD%\ComfyUI"
if not errorlevel 1 exit /b 0

call :check_root "%SCRIPT_DIR%"
if not errorlevel 1 exit /b 0

call :check_root "%SCRIPT_DIR%\ComfyUI"
if not errorlevel 1 exit /b 0

echo Could not auto-detect ComfyUI.
set /p "COMFY_ROOT=Enter the full path to the ComfyUI folder that contains main.py: "
call :check_root "%COMFY_ROOT%"
if errorlevel 1 (
    echo ERROR: "%COMFY_ROOT%" does not contain main.py.
    exit /b 1
)
exit /b 0

:check_root
set "CHECK_ROOT=%~f1"
if exist "%CHECK_ROOT%\main.py" (
    set "COMFY_ROOT=%CHECK_ROOT%"
    exit /b 0
)
exit /b 1

:find_python
set "COMFY_PARENT=%COMFY_ROOT%\.."

if exist "%COMFY_ROOT%\venv\Scripts\python.exe" (
    set "COMFY_PYTHON=%COMFY_ROOT%\venv\Scripts\python.exe"
    set "COMFY_ACTIVATE=%COMFY_ROOT%\venv\Scripts\activate.bat"
    exit /b 0
)

if exist "%COMFY_ROOT%\.venv\Scripts\python.exe" (
    set "COMFY_PYTHON=%COMFY_ROOT%\.venv\Scripts\python.exe"
    set "COMFY_ACTIVATE=%COMFY_ROOT%\.venv\Scripts\activate.bat"
    exit /b 0
)

if exist "%COMFY_PARENT%\python_embeded\python.exe" (
    set "COMFY_PYTHON=%COMFY_PARENT%\python_embeded\python.exe"
    set "COMFY_ACTIVATE="
    exit /b 0
)

if exist "%COMFY_ROOT%\python_embeded\python.exe" (
    set "COMFY_PYTHON=%COMFY_ROOT%\python_embeded\python.exe"
    set "COMFY_ACTIVATE="
    exit /b 0
)

echo ERROR: Could not find ComfyUI Python.
echo Looked for:
echo   %COMFY_ROOT%\venv\Scripts\python.exe
echo   %COMFY_ROOT%\.venv\Scripts\python.exe
echo   %COMFY_PARENT%\python_embeded\python.exe
echo   %COMFY_ROOT%\python_embeded\python.exe
exit /b 1

:activate_python
if defined COMFY_ACTIVATE (
    echo Activating ComfyUI venv...
    call "%COMFY_ACTIVATE%"
) else (
    echo Using ComfyUI portable Python.
)
exit /b 0

:install_node
set "CUSTOM_NODES=%COMFY_ROOT%\custom_nodes"
set "NODE_DIR=%CUSTOM_NODES%\%NODE_NAME%"

if not exist "%CUSTOM_NODES%" mkdir "%CUSTOM_NODES%"

if exist "%SCRIPT_DIR%\__init__.py" if exist "%SCRIPT_DIR%\diffsynth" if exist "%SCRIPT_DIR%\requirements.txt" (
    set "SCRIPT_IS_REPO=1"
)

if exist "%NODE_DIR%\.git" (
    where git >nul 2>nul
    if errorlevel 1 (
        echo ERROR: git was not found in PATH, so the existing custom node cannot be updated.
        echo Install Git for Windows or update "%NODE_DIR%" manually.
        exit /b 1
    )
    echo Updating existing custom node...
    git -C "%NODE_DIR%" pull --ff-only
    if errorlevel 1 exit /b 1
) else if exist "%NODE_DIR%\requirements.txt" (
    echo Custom node folder already exists: "%NODE_DIR%"
) else if "%SCRIPT_IS_REPO%"=="1" (
    echo Copying custom node from this folder...
    xcopy "%SCRIPT_DIR%" "%NODE_DIR%\" /E /I /Y /Q >nul
    if errorlevel 1 exit /b 1
) else (
    where git >nul 2>nul
    if errorlevel 1 (
        echo ERROR: git was not found in PATH.
        echo Install Git for Windows, then run this installer again.
        exit /b 1
    )
    echo Cloning custom node...
    git clone "%REPO_URL%" "%NODE_DIR%"
    if errorlevel 1 exit /b 1
)

echo Installing custom node Python requirements...
"%COMFY_PYTHON%" -m pip install -r "%NODE_DIR%\requirements.txt"
if errorlevel 1 exit /b 1

exit /b 0

:download_models
where curl >nul 2>nul
if errorlevel 1 (
    echo ERROR: curl.exe was not found in PATH.
    echo Windows 10/11 normally includes curl. Install curl or download the models manually.
    exit /b 1
)

if not exist "%COMFY_ROOT%\models\diffusion_models" mkdir "%COMFY_ROOT%\models\diffusion_models"
if not exist "%COMFY_ROOT%\models\text_encoders" mkdir "%COMFY_ROOT%\models\text_encoders"
if not exist "%COMFY_ROOT%\models\text_encoders\Z-Image-Turbo-tokenizer\tokenizer" mkdir "%COMFY_ROOT%\models\text_encoders\Z-Image-Turbo-tokenizer\tokenizer"

call :download_file "Z-Image 6B no-VAE model" "https://huggingface.co/zhen-nan/L2P/resolve/main/model-1k-merge.safetensors" "%COMFY_ROOT%\models\diffusion_models\Z-image-6b-no-VAE.safetensors"
if errorlevel 1 exit /b 1

call :download_file "Qwen 3 4B text encoder" "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors" "%COMFY_ROOT%\models\text_encoders\qwen_3_4b.safetensors"
if errorlevel 1 exit /b 1

call :download_file "Tokenizer merges" "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/tokenizer/merges.txt" "%COMFY_ROOT%\models\text_encoders\Z-Image-Turbo-tokenizer\tokenizer\merges.txt"
if errorlevel 1 exit /b 1

call :download_file "Tokenizer JSON" "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/tokenizer/tokenizer.json" "%COMFY_ROOT%\models\text_encoders\Z-Image-Turbo-tokenizer\tokenizer\tokenizer.json"
if errorlevel 1 exit /b 1

call :download_file "Tokenizer config" "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/tokenizer/tokenizer_config.json" "%COMFY_ROOT%\models\text_encoders\Z-Image-Turbo-tokenizer\tokenizer\tokenizer_config.json"
if errorlevel 1 exit /b 1

call :download_file "Tokenizer vocab" "https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/resolve/main/tokenizer/vocab.json" "%COMFY_ROOT%\models\text_encoders\Z-Image-Turbo-tokenizer\tokenizer\vocab.json"
if errorlevel 1 exit /b 1

exit /b 0

:download_file
set "LABEL=%~1"
set "URL=%~2"
set "DEST=%~3"

if exist "%DEST%" if "%FORCE%"=="0" (
    echo [SKIP] %LABEL% already exists:
    echo   "%DEST%"
    exit /b 0
)

if exist "%DEST%" if "%FORCE%"=="1" del /f /q "%DEST%"

echo [DOWNLOADING] %LABEL%
echo   %URL%
echo   to "%DEST%"
curl.exe -L --fail --retry 3 --continue-at - --output "%DEST%" "%URL%"
if errorlevel 1 (
    echo [ERROR] Download failed for %LABEL%.
    exit /b 1
)
echo [DONE] %LABEL%
exit /b 0
