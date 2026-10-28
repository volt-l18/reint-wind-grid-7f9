import os

class Config:
    ELEXON_BASE_URL = os.getenv("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1")
    CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "elexon_cache.db"))
    DEFAULT_MONTH = "2026-01"
    # UK Day-Ahead wholesale market gate closure is typically 12:00 PM (noon) on D-1
    GATE_CLOSURE_HOUR = int(os.getenv("GATE_CLOSURE_HOUR", 12))
