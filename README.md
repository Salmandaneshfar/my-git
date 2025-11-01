# Automated Git Commiter

اسکریپت خودکار برای ساخت commit های git در بازه زمانی مشخص.

## ویژگی‌ها

✅ **رابط گرافیکی (GUI)** - رابط کاربری آسان با tkinter  
✅ **مدیریت چند Repository** - اضافه و مدیریت چندین repository  
✅ **تنظیمات جداگانه** - هر repository فایل تنظیمات مخصوص خودش  
✅ **پشتیبانی از خط فرمان** - تنظیمات از طریق آرگومان‌ها  
✅ **فایل تنظیمات** - استفاده از `config.json`  
✅ **Cross-platform** - کار روی Windows و Linux  
✅ **Dry-run mode** - تست بدون ساخت commit واقعی  
✅ **Auto-push** - پشتیبانی از push خودکار به remote  

## نصب

1. نصب وابستگی‌ها:
```bash
pip install -r req.txt
```

## استفاده

### 🖥️ روش 0: رابط گرافیکی (GUI) - **پیشنهادی**

ساده‌ترین روش استفاده، رابط گرافیکی است:

```bash
python commiter_gui.py
```

یا در Windows:
```bash
run_gui.bat
```

**ویژگی‌های GUI:**
- ✅ مدیریت چندین repository
- ✅ انتخاب repository از لیست dropdown
- ✅ تنظیمات جداگانه برای هر repository
- ✅ ذخیره/بارگذاری خودکار تنظیمات
- ✅ تقویم برای انتخاب تاریخ
- ✅ لاگ زنده پیشرفت
- ✅ دکمه توقف در حین اجرا

**نحوه استفاده GUI:**
1. دکمه "➕ افزودن" را بزنید و پوشه repository را انتخاب کنید
2. بازه تاریخی را از تقویم‌ها انتخاب کنید
3. تنظیمات commit را تنظیم کنید
4. دکمه "▶️ شروع ساخت Commit" را بزنید
5. تنظیمات به صورت خودکار برای هر repository ذخیره می‌شود

---

### روش 1: استفاده از تنظیمات پیش‌فرض
```bash
python commiter.py
```

### روش 2: تنظیم از طریق آرگومان‌ها
```bash
# تعیین بازه تاریخی
python commiter.py --start 2025-01-01 --end 2025-01-31

# تعیین مسیر repository
python commiter.py --repo "D:\my project\my-git"

# Push خودکار
python commiter.py --push

# تست بدون commit واقعی
python commiter.py --dry-run

# تغییر احتمال skip روزها
python commiter.py --skip-prob 0.3

# تغییر تعداد commit‌ها
python commiter.py --min-commits 2 --max-commits 8
```

### روش 3: استفاده از فایل تنظیمات
فایل `config.json` را ویرایش کنید و سپس:
```bash
python commiter.py
```

یا فایل تنظیمات سفارشی:
```bash
python commiter.py --config my_custom_config.json
```

## فایل تنظیمات (config.json)

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "skip_probability": 0.2,
  "min_commits": 1,
  "max_commits": 6,
  "auto_push": false,
  "repo_path": null
}
```

### پارامترها:
- `start_date`: تاریخ شروع (فرمت: YYYY-MM-DD)
- `end_date`: تاریخ پایان (فرمت: YYYY-MM-DD)
- `skip_probability`: احتمال skip کردن یک روز (0.0 تا 1.0)
- `min_commits`: حداقل commit در هر روز
- `max_commits`: حداکثر commit در هر روز
- `auto_push`: آیا بعد از commit ها push کند؟ (true/false)
- `repo_path`: مسیر repository (null = دایرکتوری فعلی)

## خودکارسازی (Scheduling)

### Windows Task Scheduler

1. Task Scheduler را باز کنید
2. "Create Basic Task" را انتخاب کنید
3. نام و توضیحات را وارد کنید
4. Trigger (زمان اجرا) را تنظیم کنید (مثلاً روزانه)
5. Action: "Start a program" را انتخاب کنید
6. Program/script: `run_commiter.bat` یا مسیر کامل به `python.exe`
7. Add arguments: `commiter.py` (یا آرگومان‌های مورد نیاز)
8. Start in: مسیر پروژه شما

یا می‌توانید از `run_commiter.bat` استفاده کنید:
```
C:\path\to\python.exe C:\path\to\commiter.py --start 2025-01-01 --end 2025-01-31
```

### Linux/Mac Cron

برای اجرای روزانه در ساعت 9 صبح:
```bash
crontab -e
```

سپس این خط را اضافه کنید:
```
0 9 * * * cd /path/to/project && /usr/bin/python3 commiter.py
```

## مثال‌ها

```bash
# ساخت commit برای یک ماه با 3-10 commit در هر روز
python commiter.py --start 2025-01-01 --end 2025-01-31 --min-commits 3 --max-commits 10

# فقط تست - بدون commit واقعی
python commiter.py --start 2025-01-01 --end 2025-01-31 --dry-run

# Push خودکار بعد از commit
python commiter.py --start 2025-01-01 --end 2025-01-31 --push

# استفاده از repository متفاوت
python commiter.py --repo "C:\my-repo" --start 2025-01-01 --end 2025-01-31
```

## نکات مهم

- مسیر repository به صورت خودکار از دایرکتوری فعلی استفاده می‌شود (اگر مشخص نشده باشد)
- برای اولین اجرا، repository باید initialize شده باشد
- در حالت dry-run، هیچ تغییری در git ایجاد نمی‌شود
- Commit‌ها با تاریخ و زمان واقعی (طبق بازه زمانی) ایجاد می‌شوند

