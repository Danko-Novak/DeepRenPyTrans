"""
Configuration loader for DeepRenPyTrans.
Merges config.yaml defaults with environment variables.
"""

import os
import yaml
from dotenv import load_dotenv

# Default configuration
DEFAULTS = {
    "game_dir": ".",
    "target_language": "Russian",
    "translation_dir": "russian",
    "api": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "temperature": 0.2,
        "batch_size": 40,
        "max_retries": 3,
        "delay": 1.0,
    },
    "fonts": {
        "default": "DejaVuSans.ttf",
        "replacements": {},
    },
    "extraction": {
        "skip_prefixes": [
            "ITM", "ACT", "SSID", "QST", "LID", "SEID", "SUID",
            "LOC", "GUI", "VID", "AE", "JOB", "DIA", "SBP", "GID",
        ],
        "force_include": [],
        "force_exclude": [],
        "min_length": 2,
    },
    "hooks": {
        "toggle_hotkey": "l",
        "auto_set_language": True,
    },
}

# Provider → (env var name, base URL)
PROVIDER_MAP = {
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1/chat/completions",
    },
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1/chat/completions",
    },
    "openrouter": {
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
    },
    "groq": {
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
    },
    "nebius": {
        "env_key": "NEBIUS_API_KEY",
        "base_url": "https://api.studio.nebius.ai/v1/chat/completions",
    },
    "deepinfra": {
        "env_key": "DEEPINFRA_API_KEY",
        "base_url": "https://api.deepinfra.com/v1/openai/chat/completions",
    },
    "ollama": {
        "env_key": None,
        "base_url": "http://localhost:11434/v1/chat/completions",
    },
}


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base, returning a new dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str = None) -> dict:
    """
    Load configuration from YAML file and environment variables.
    
    Priority: CLI args > env vars > config.yaml > defaults
    """
    # Load .env file if present
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    # Start with defaults
    config = DEFAULTS.copy()
    
    # Merge YAML config if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
        config = deep_merge(config, yaml_config)
    
    # Resolve API key from environment
    provider = config["api"]["provider"]
    provider_info = PROVIDER_MAP.get(provider, PROVIDER_MAP["deepseek"])
    
    if provider_info["env_key"]:
        api_key = os.environ.get(provider_info["env_key"], "")
        config["api"]["api_key"] = api_key
    else:
        config["api"]["api_key"] = ""
    
    config["api"]["base_url"] = provider_info["base_url"]
    
    return config
