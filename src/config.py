import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-pro"  # deepseek-chat depreciado em 25/07/2026

# Baserow
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN", "")
BASEROW_BASE_URL = "https://base.duobro.com.br/api"
BASEROW_TABLE_ID = 828
BASEROW_DB_ID = 192

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID", "0"))
TELEGRAM_TOPIC_DIARIO = int(os.getenv("TELEGRAM_TOPIC_DIARIO", "4"))
TELEGRAM_TOPIC_DOMINICAL = int(os.getenv("TELEGRAM_TOPIC_DOMINICAL", "3"))
TELEGRAM_ADMIN_DM = int(os.getenv("TELEGRAM_ADMIN_DM", "0"))
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Matos Soares
MATOS_SOARES_BASE = os.getenv("MATOS_SOARES_BASE", "http://matos-soares")
CALENDARIO_URL = f"{MATOS_SOARES_BASE}:8651/"
SANTOS_URL = f"{MATOS_SOARES_BASE}:8652/santos"
BIBLIA_URL = f"{MATOS_SOARES_BASE}:8650/query-matos"

# Health
HEALTH_PORT = 8660

# Timezone
TIMEZONE = "America/Sao_Paulo"

# Scheduler
CRON_DIARIO = {"day_of_week": "mon-sat", "hour": 6, "minute": 0}
CRON_DOMINICAL = {"day_of_week": "sun", "hour": 6, "minute": 0}
