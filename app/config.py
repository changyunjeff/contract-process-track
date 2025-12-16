from __future__ import annotations
from pydantic_yaml import parse_yaml_file_as, parse_yaml_raw_as, to_yaml_file
from typing import Dict
import yaml
import os

from app.configs import AppConfig, RedisConfig, PostgresConfig
from app.configs import GlobalConfig


def _get_config_file(env: str) -> str | None:
    """
    1. According to the environment variable, get the configuration file path.

    2. If the environment variable is not set, use the default configuration file path.

    3. If the configuration file does not exist, return None.
    """

    config_mapping = {
        "dev": "config.dev.yaml",
        "development": "config.dev.yaml",
        "prod": "config.prod.yaml",
        "production": "config.prod.yaml",
        "test": "config.test.yaml",
        "testing": "config.test.yaml",
    }
    config_path = config_mapping.get(env, "config.dev.yaml")
    # Resolve to absolute path if relative
    config_path = os.path.abspath(config_path)

    # Check file existence
    if os.path.exists(config_path) and os.path.isfile(config_path):
        return config_path
    else:
        return None

def _ensure_open_with_utf8(config_file: str) -> str:
    """
    Ensure the configuration file is opened with UTF-8 encoding.
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            "utf-8",
            b"",
            0,
            1,
            f"Configuration file is not a valid UTF-8 encoded file: {config_file}"
        ) from e

def load_config(config_path: str | None = None) -> GlobalConfig:
    """Load configuration from file or environment variables."""
    env = os.getenv("MODE", "dev").lower()
    config_file = config_path
    if config_file is None:
        config_file = _get_config_file(env)
    if config_file is None:
        raise FileNotFoundError(f"Configuration file not found for environment: {env}")
    
    try:
        config_data = _ensure_open_with_utf8(config_file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Configuration file not found: {config_file}") from e
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            "utf-8",
            b"",
            0,
            1,
            f"Configuration file is not a valid UTF-8 encoded file: {config_file}"
        ) from e

    try:
        # Parse YAML content
        yaml.safe_load(config_data)  # Validate YAML syntax first
        config = parse_yaml_raw_as(GlobalConfig, config_data)
        return config
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Configuration file is not a valid YAML file: {config_file}") from e
    except Exception as e:
        print(f"❌ 预加载配置失败：{str(e)}")
        raise RuntimeError(f"❌ 预加载配置失败：{str(e)}") from e

_global_config = None

def get_global_config() -> GlobalConfig:
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config

def get_app_config() -> AppConfig:
    return get_global_config().app

def get_redis_config() -> RedisConfig | None:
    """Get Redis configuration from global config."""
    return get_global_config().redis


def get_postgres_config(db_name: str | None = None) -> PostgresConfig | None:
    """
    Get PostgreSQL configuration from global config.
    
    Args:
        db_name: Database name (e.g., 'company_info_cn', 'law_cn'). 
                 If None, returns the first database config or legacy postgres config.
    
    Returns:
        PostgresConfig or None if not found
    """
    global_config = get_global_config()
    
    # 优先使用新的 databases 配置
    if global_config.databases:
        if db_name:
            return global_config.databases.get(db_name)
        # 如果没有指定 db_name，返回第一个数据库配置
        if global_config.databases:
            return next(iter(global_config.databases.values()))
    
    # 向后兼容：如果没有 databases 配置，使用旧的 postgres 配置
    return global_config.postgres


def get_all_database_configs() -> Dict[str, PostgresConfig]:
    """
    Get all database configurations.
    
    Returns:
        Dictionary mapping database names to PostgresConfig
    """
    global_config = get_global_config()
    
    if global_config.databases:
        return global_config.databases
    
    # 向后兼容：如果没有 databases 配置，使用旧的 postgres 配置
    result = {}
    if global_config.postgres:
        # 使用数据库名作为 key，如果没有则使用 'default'
        db_name = global_config.postgres.database or 'default'
        result[db_name] = global_config.postgres
    return result
