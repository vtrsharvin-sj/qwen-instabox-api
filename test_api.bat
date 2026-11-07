@echo off
setlocal enabledelayedexpansion

set API_URL=https://8000-agq3kirkx25dxx5s7haejfgk4a.instabox.tech

echo ============================================
echo   Qwen3.5-4B Uncensored API - Test Suite
echo ============================================
echo API: %API_URL%
echo.

:: ── Check if curl is available ───────────────────────────────────────────────
where curl >nul 2>&1
if errorlevel 1 (
    echo [ERROR] curl not found. Install it or use Windows 10 1803+ which includes curl.
    pause & exit /b 1
)

:: ── Test 1: Health check ─────────────────────────────────────────────────────
echo [1/3] Health check (GET /) ...
curl -s --max-time 10 "%API_URL%/" 
echo.
echo.

:: ── Test 2: List models ──────────────────────────────────────────────────────
echo [2/3] List models (GET /v1/models) ...
curl -s --max-time 10 "%API_URL%/v1/models"
echo.
echo.

:: ── Test 3: Chat completion ──────────────────────────────────────────────────
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
