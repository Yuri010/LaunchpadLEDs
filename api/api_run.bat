@echo off
title LaunchpadLEDs - API
cd "%~dp0"
cd ..
set PYTHONPATH=%cd%
uvicorn api.api:app --reload