# ========================================
# تنظیمات امنیتی پروژه
# ========================================

SECRET_KEY = "your-secret-key-here-change-it-in-production"  # کلید مخفی برای امضای JWT
ALGORITHM = "HS256"                                           # الگوریتم رمزنگاری
ACCESS_TOKEN_EXPIRE_MINUTES = 30                              # مدت اعتبار توکن (دقیقه)