@echo off
setlocal enabledelayedexpansion

set API_URL=https://qwen-api.vtrsharvin.workers.dev
set API_KEY=YOUR_API_KEY

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

echo [1/3] Health check (GET /docs) ...
curl -s --max-time 10 -o nul -w "Status: %%{http_code}" "%API_URL%/docs"
echo.
echo.

echo [2/3] List models (GET /v1/models) ...
curl -s --max-time 10 "%API_URL%/v1/models" -H "Authorization: Bearer %API_KEY%"
echo.
echo.

echo [3/3] Chat completion (POST /v1/chat/completions) ...
echo Sending: "What is 2 + 2? Answer in one sentence."
echo (this may take 20-60 seconds on CPU...)
echo.

curl -s --max-time 120 ^
  -X POST "%API_URL%/v1/chat/completions" ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer %API_KEY%" ^
  -d "{\"model\":\"qwen3.5-4b-uncensored\",\"messages\":[{\"role\":\"user\",\"content\":\"What is 2 + 2? Answer in one sentence.\"}],\"max_tokens\":100,\"temperature\":0.7}"

echo.
echo.
echo ============================================
echo   All tests done.
echo ============================================
pause
