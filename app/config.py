from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 3600
    RATELIMIT_DEFAULT = "30 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
