@echo off
cd "c:\Users\nacho\Desktop\chatbot\chatbot"
call venv\Scripts\activate.bat
cd backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
