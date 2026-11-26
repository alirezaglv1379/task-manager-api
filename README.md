# Task Manager — Full Stack

یک برنامه مدیریت وظایف با بک‌اند FastAPI و فرانت‌اند React + TypeScript. رابط کاربری فارسی و راست‌به‌چپ است و بک‌اند از SQLite، SQLAlchemy و Alembic استفاده می‌کند.

## قابلیت‌ها

- ثبت‌نام و ورود با JWT
- Access Token با اعتبار ۳۰ دقیقه و Refresh Token هفت‌روزه در کوکی `HttpOnly`
- چرخش Refresh Token و ابطال نشست هنگام خروج
- محدودیت تلاش ورود بر اساس IP و نام کاربری
- مالکیت وظایف و جلوگیری از دسترسی به اطلاعات دیگر کاربران
- عملیات CRUD، ویرایش کامل PUT و ویرایش جزئی PATCH
- فیلتر وضعیت، صفحه‌بندی سمت سرور و مرتب‌سازی
- ذخیره زمان بر اساس UTC و نمایش زمان محلی در مرورگر
- Migration دیتابیس با Alembic و پشتیبان‌گیری قبل از ارتقای دیتابیس قدیمی
- تست‌های خودکار، Ruff، pip-audit و GitHub Actions

## ساختار مخزن

```text
backend/       FastAPI, SQLAlchemy, Alembic, tests
frontend/      React, TypeScript, Vite
scripts/       اسکریپت‌های اجرای توسعه
 docs/         مستندات فنی و راهنمای فارسی
.github/       گردش‌کار CI
```

## شروع سریع

راهنمای کامل نصب ویندوز و لینوکس در [docs/SETUP.md](docs/SETUP.md) قرار دارد. برای شروع توسعه:

1. فایل `.env.example` را به `backend/.env` کپی و `SECRET_KEY` را با یک مقدار تصادفی قوی جایگزین کنید.
2. در پوشه `backend` محیط مجازی بسازید و وابستگی‌ها را نصب کنید.
3. `python -m scripts.migrate_db` را اجرا کنید.
4. سرور را با `uvicorn main:app --reload` اجرا کنید.
5. در پوشه `frontend` دستورهای `npm install` و `npm run dev` را اجرا کنید.

آدرس‌های توسعه:

- Frontend: http://localhost:5173
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## مستندات

- [راهنمای نصب فارسی و انگلیسی](docs/SETUP.md)
- [راهنمای استفاده فارسی](docs/USER_GUIDE_FA.md)
- [تصمیم‌های تأییدشده ۱۶گانه](docs/DECISIONS.md)
- [معماری](docs/ARCHITECTURE.md)
- [قرارداد API](docs/API.md)
- [ساختار دیتابیس](docs/DATABASE.md)
- [Migration و پشتیبان‌گیری](docs/MIGRATIONS.md)
- [امنیت](docs/SECURITY.md)
- [تست و کنترل کیفیت](docs/TESTING.md)
- [گزارش اعتبارسنجی این بسته](docs/VALIDATION_REPORT.md)
- [تغییرات نسخه](docs/CHANGELOG.md)

## وضعیت اعتبارسنجی

آخرین بررسی‌های محلی در تاریخ 2026-11-26:

| بررسی | نتیجه |
|---|---|
| Backend dependency installation | موفق |
| Backend pip check | بدون ناسازگاری |
| Ruff | موفق |
| Backend tests | ۳۳ تست موفق |
| Backend coverage | ۸۴.۰۵٪ |
| Backend pip-audit | صفر آسیب‌پذیری شناخته‌شده |
| Fresh SQLite migration | موفق |
| Alembic head | 0003_task_indexes |
| Frontend npm ci | موفق |
| Frontend npm audit | صفر آسیب‌پذیری |
| Frontend tests | ۴ تست موفق |
| Frontend production build | موفق |

تمام بررسی‌های محلی فوق با موفقیت انجام شده‌اند.

اجرای نهایی GitHub Actions روی شاخه fullstack-upgrade هنوز در انتظار تأیید است.

تا پیش از موفقیت کامل CI، این نسخه را انتشار نهایی یا Production Ready تلقی نکنید.