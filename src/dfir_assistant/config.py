"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with env override support.
    
    Settings are loaded from:
    1. Default values
    2. config/settings.yaml (if exists)
    3. Environment variables (DFIR_ prefix)
    """
    
    model_config = SettingsConfigDict(
        env_prefix="DFIR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:32b-instruct-q4_K_M"
    embedding_model: str = "nomic-embed-text"
    temperature: float = 0.1
    max_tokens: int = 4096
    
    # Fallback models (in priority order)
    fallback_models: list[str] = [
        "qwen2.5:14b-instruct-q4_K_M",
        "qwen2.5:7b-instruct-q8_0",
    ]
    
    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "dfir_books"
    
    # Search Configuration
    search_dense_weight: float = 0.4
    search_sparse_weight: float = 0.6
    top_k: int = 15
    rerank_top_k: int = 5
    
    # Chunking Configuration
    chunk_size: int = 512
    chunk_overlap: int = 100
    
    # Confidence Thresholds
    min_confidence: float = 0.5
    warn_confidence: float = 0.7
    
    # VRAM Monitoring
    vram_warning_threshold_gb: float = 22.0
    vram_critical_threshold_gb: float = 23.0
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    audit_log_file: str = "logs/audit.log"
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 7860


def load_yaml_config(config_path: Path | str = "config/settings.yaml") -> dict[str, Any]:
    """Load configuration from YAML file."""
    config_path = Path(config_path)
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Settings are loaded from YAML first, then overridden by environment variables.
    """
    yaml_config = load_yaml_config()
    return Settings(**yaml_config)
