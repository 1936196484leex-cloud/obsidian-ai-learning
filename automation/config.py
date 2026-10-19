"""Configuration is resolved relative to these scripts, never the shell cwd."""
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent

def settings():
    from dotenv import load_dotenv
    load_dotenv(BASE / '.env', override=False)
    raw = os.getenv('DRY_RUN', 'true').lower()
    if raw not in ('true', 'false'):
        raise ValueError('DRY_RUN must be true or false')
    vault = Path(os.getenv('VAULT_PATH') or BASE.parent).expanduser().resolve()
    if not (vault / '01 Daily').is_dir():
        raise ValueError('VAULT_PATH must contain 01 Daily')
    return vault, raw == 'true'
