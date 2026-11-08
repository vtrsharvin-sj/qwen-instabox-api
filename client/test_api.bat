@echo off
setlocal enabledelayedexpansion

:: Replace with your Instabox port tunnel URL
set API_URL=https://qwen-api.vtrsharvin.workers.dev

echo ============================================
echo   Qwen3.5-4B Uncensored API - Test Suite
echo ============================================
echo API: %API_URL%
echo.

where curl >nul 2>&1
if errorlevel 1 (
    echo [ERROR] curl not found. Requires Windows 10 1803+.
    pause & exit /b 1
)

echo [1/3] Health check (GET /) ...
curl -s --max-time 10 "%API_URL%/"
echo.
echo.

echo [2/3] List models (GET /v1/models) ...
curl -s --max-time 10 "%API_URL%/v1/models"
echo.
echo.

echo [3/3] Chat completion (POST /v1/chat/completions) ...
echo Sending: "What is 2 + 2? Answer in one sentence."
echo (this may take 20-60 seconds on CPU...)
echo.

curl -s --max-time 120 ^
  -X POST "%API_URL%/v1/chat/completions" ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen3.5-4b-uncensored\",\"messages\":[{\"role\":\"user\",\"content\":\"What is 2 + 2? Answer in one sentence.\"}],\"max_tokens\":100,\"temperature\":0.7}"

echo.
echo.
echo ============================================
echo   All tests done.
echo ============================================
pause
