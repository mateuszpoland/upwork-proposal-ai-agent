"""
Configuration loader that supports both environment variables and AWS Secrets Manager.
Prioritizes environment variables first, then falls back to Secrets Manager.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Load configuration from environment variables or AWS Secrets Manager."""
    
    def __init__(self, secret_name: Optional[str] = None, region_name: str = "eu-central-1"):
        """
        Initialize the config loader.
        
        Args:
            secret_name: Name of the AWS secret. If None, will try to get from env or use default.
            region_name: AWS region for Secrets Manager.
        """
        self.region_name = region_name
        self.secret_name = secret_name or os.getenv('AWS_SECRET_NAME', 'rag-worker-app-secrets-prod')
        self._secrets_cache: Optional[Dict[str, Any]] = None
        self._secrets_client = None
    
    def _get_secrets_client(self):
        """Get or create Secrets Manager client."""
        if self._secrets_client is None:
            try:
                self._secrets_client = boto3.client('secretsmanager', region_name=self.region_name)
            except NoCredentialsError:
                logger.warning("No AWS credentials found. Will use environment variables only.")
                self._secrets_client = False  # Mark as unavailable
        return self._secrets_client
    
    def _load_secrets_from_aws(self) -> Optional[Dict[str, Any]]:
        """Load secrets from AWS Secrets Manager."""
        if self._secrets_cache is not None:
            return self._secrets_cache
        
        client = self._get_secrets_client()
        if not client:
            return None
        
        try:
            response = client.get_secret_value(SecretId=self.secret_name)
            secret_string = response['SecretString']
            self._secrets_cache = json.loads(secret_string)
            logger.info(f"Successfully loaded secrets from AWS Secrets Manager: {self.secret_name}")
            return self._secrets_cache
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.warning(f"Secret {self.secret_name} not found in AWS Secrets Manager")
            elif error_code == 'InvalidRequestException':
                logger.warning(f"Invalid request for secret {self.secret_name}")
            elif error_code == 'InvalidParameterException':
                logger.warning(f"Invalid parameter for secret {self.secret_name}")
            else:
                logger.error(f"Error loading secrets from AWS: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading secrets from AWS: {e}")
            return None
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get configuration value.
        
        Priority:
        1. Environment variable
        2. AWS Secrets Manager
        3. Default value
        
        Args:
            key: Configuration key name
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # First try environment variable
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
        
        # Then try AWS Secrets Manager
        secrets = self._load_secrets_from_aws()
        if secrets and key in secrets:
            return secrets[key]
        
        # Finally return default
        return default
    
    def get_required(self, key: str) -> str:
        """
        Get required configuration value.
        
        Raises ValueError if key is not found in any source.
        
        Args:
            key: Configuration key name
            
        Returns:
            Configuration value
            
        Raises:
            ValueError: If key is not found
        """
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required configuration key '{key}' not found in environment variables or AWS Secrets Manager")
        return value
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get integer configuration value."""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}")
            return default
    
    def update_secret(self, updates: Dict[str, str]) -> bool:
        """
        Update values in AWS Secrets Manager.
        
        Args:
            updates: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise
        """
        client = self._get_secrets_client()
        if not client:
            logger.error("AWS Secrets Manager client not available")
            return False
        
        try:
            # Get current secret value
            current_secrets = self._load_secrets_from_aws() or {}
            
            # Update with new values
            current_secrets.update(updates)
            
            # Update the secret
            client.update_secret(
                SecretId=self.secret_name,
                SecretString=json.dumps(current_secrets, indent=2)
            )
            
            # Clear cache to force reload
            self._secrets_cache = None
            
            logger.info(f"Successfully updated secret {self.secret_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating secret: {e}")
            return False

# Global config loader instance
config = ConfigLoader()