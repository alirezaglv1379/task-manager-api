# نصب و راه‌اندازی / Setup Guide

## Requirements

- Python 3.11 یا 3.12 (نسخه‌های جدیدتر فقط پس از اجرای ماتریس تست)
- Node.js 20 LTS یا جدیدتر و npm
- Windows 10/11 یا Linux/macOS

## Windows PowerShell

از ریشه پروژه:

```powershell
Copy-Item .env.example backend/.env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

مقدار تولیدشده را در `backend/.env` مقابل `SECRET_KEY` قرار دهید. سپس:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m scripts.migrate_db
uvicorn main:app --reload
```

در پنجره PowerShell دوم:

```powershell
cd frontend
npm install
npm run dev
```

اگر PowerShell اجرای اسکریپت فعال‌سازی را مسدود کرد، فقط برای همان نشست اجرا کنید:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Linux / macOS

```bash
cp .env.example backend/.env
python -c 'import secrets; print(secrets.token_urlsafe(48))'
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m scripts.migrate_db
uvicorn main:app --reload
```

در ترمینال دوم:

```bash
cd frontend
npm install
npm run dev
```

## URLs

- UI: http://localhost:5173
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health: http://127.0.0.1:8000/health

## Existing database from the original project

اگر فایل SQLite قدیمی دارید، آن را در مسیری قرار دهید که `DATABASE_URL` به آن اشاره می‌کند. سپس از پوشه `backend` اجرا کنید:

```bash
python -m scripts.migrate_db
```

اسکریپت ساختار قدیمی `users` و `tasks` را بررسی می‌کند، قبل از تغییر یک نسخه پشتیبان با نام زمان‌دار می‌سازد، نسخه پایه را فقط پس از تطبیق ساختار ثبت می‌کند و Migrationهای بعدی را اجرا می‌کند. اگر ساختار ناشناخته یا ناقص باشد، عملیات متوقف می‌شود و دیتابیس دست‌نخورده می‌ماند.

## Production deployment notes

- `ENVIRONMENT=production`
- `SECRET_KEY` تصادفی و قوی، فقط در secret manager یا environment variables
- `COOKIE_SECURE=true` و HTTPS الزامی
- `CORS_ORIGINS` و `CSRF_TRUSTED_ORIGINS` فقط شامل Origin واقعی فرانت‌اند
- فرانت‌اند و API را پشت یک reverse proxy و روی یک origin ارائه کنید تا کوکی Refresh هم‌مبدأ باشد.
- `allow_credentials=False` عمداً حفظ شده است؛ جریان Refresh در معماری پیشنهادی same-origin است.
- فقط در صورت وجود reverse proxy مورد اعتماد، IP آن را در `TRUSTED_PROXY_IPS` قرار دهید.
- فایل SQLite و backupها را خارج از پوشه عمومی وب نگهداری کنید.

## Dependency lock

فایل lock نهایی باید در یک virtual environment تمیز و پس از حل موفق وابستگی‌ها تولید شود. پس از نصب موفق روی نسخه Python هدف:

```bash
python -m pip freeze --local > requirements.lock
```

این دستور را در محیط مجازی تمیز اجرا کنید تا بسته‌های نامرتبط سیستم وارد lock نشوند. فایل lock تولیدشده را همراه تغییرات پروژه commit کنید.
