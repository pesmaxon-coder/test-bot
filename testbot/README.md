# 🎓 Online Test Bot

## 🚀 Ishga tushirish

### 1. O'rnatish:
```
pip install -r requirements.txt
```

### 2. config.py ni sozlash:
```python
BOT_TOKEN = "BotFather dan olingan token"
ADMIN_IDS = [sizning_telegram_id]
REQUIRED_CHANNELS = [
    {"name": "Kanal nomi", "username": "@kanal", "url": "https://t.me/kanal"},
]
```

### 3. Ishga tushirish:
```
python bot.py
```

---

## 📋 Funksiyalar

| Funksiya | Tavsif |
|----------|--------|
| ✍️ Ro'yxatdan o'tish | Ism, familiya, telefon |
| 🔔 Majburiy obuna | Kanallarga a'zolik tekshiruvi |
| ✍️ Test yaratish | Javob kalitlari → ID olish |
| ✅ Javob tekshirish | ID + javoblar → sertifikat |
| 🎨 8 xil dizayn | Sozlamalardan tanlash |
| 🎉 Natijalar | Barcha o'tgan testlar |

---

## 🎯 Test formati

**Yaratuvchi uchun:**
- Javoblarni yuboring: `ABCDDCBAABCD` yoki `1A 2B 3C 4D`
- Bot sizga 7 belgili ID beradi: `ABC1234`
- Bu ID ni kanalga joylashtiring

**Ishtirokchilar uchun:**
- ID ni kiriting → javoblarni yuboring
- Bot tekshiradi → sertifikat beradi
