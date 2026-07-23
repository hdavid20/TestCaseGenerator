import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "data", "config.json")

DEFAULT_CONFIG = {
    "api_key": "",
    "model": "gemini-2.0-flash",
    "language": "es",
    "project_key": "",
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def get_api_key():
    return os.environ.get("GEMINI_API_KEY") or load_config().get("api_key", "")
