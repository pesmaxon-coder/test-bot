import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8517462613:AAHYWPrkstm2axeQ9cS_faSTouTwebRa130")

ADMIN_IDS = [5420944421, 582974676]  # O'z Telegram ID ingiz

# Majburiy a'zo bo'lish kanallari - o'zingiznikini yozing
REQUIRED_CHANNELS = [
    {
        "name": "CEFR_team",
        "username": "@CEFRteam",
        "url": "https://t.me/CEFRteam"
    },
    {
        "name": "Abbos Mehmonaliyev",
        "username": "@abbos_mekhmonaliev",
        "url": "https://t.me/abbos_mekhmonaliev"
    },
]

DB_PATH = os.getenv("DB_PATH", "/app/data/testbot.db")
CERT_DIR = "certificates"
DEFAULT_AUTHOR = "Test Muallifi"
