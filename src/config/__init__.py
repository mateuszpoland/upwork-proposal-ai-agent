"""Configuration module for loading secrets and environment variables."""

from .secrets_manager import config, ConfigLoader

__all__ = ['config', 'ConfigLoader']