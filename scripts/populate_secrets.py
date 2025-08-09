#!/usr/bin/env python3
"""
Script to populate AWS Secrets Manager with environment variables from .env.local
"""

import os
import json
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

def load_env_file(file_path: str) -> dict:
    """Load environment variables from file."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        sys.exit(1)
    
    load_dotenv(file_path)
    
    # List of environment variables from .env.local
    env_vars = [
        'APP_RELEASE',
        'SAGEMAKER_ENDPOINT_NAME',
        'BASIC_AUTH_ADMIN_USER',
        'BASIC_AUTH_ADMIN_PASS',
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'COHERE_API_KEY',
        'OPENAI_EMBEDDING_MODEL',
        'OPENAI_MODEL',
        'PHOENIX_PROJECT_NAME',
        'OTEL_EXPORTER_OTLP_HEADERS',
        'PHOENIX_CLIENT_HEADERS',
        'PHOENIX_COLLECTOR_ENDPOINT',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SUPABASE_PASSWORD',
        'WEBHOOK_URL',
        'WEBHOOK_USER',
        'WEBHOOK_PASS',
        'BASIC_AUTH_USER',
        'BASIC_AUTH_PASS',
        'DEBUGPY_ENABLED',
        'PYDEVD_DISABLE_FILE_VALIDATION',
        'ENABLE_PROFILING'
    ]
    
    secrets = {}
    for var in env_vars:
        value = os.getenv(var)
        if value is not None and value.strip():  # Only include non-empty values
            secrets[var] = value
    
    return secrets

def update_secret(secret_name: str, secrets: dict, region: str = 'eu-central-1'):
    """Update AWS Secrets Manager secret."""
    client = boto3.client('secretsmanager', region_name=region)
    
    try:
        # Try to get existing secret
        try:
            response = client.get_secret_value(SecretId=secret_name)
            existing_secrets = json.loads(response['SecretString'])
            print(f"Found existing secret: {secret_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                existing_secrets = {}
                print(f"Secret {secret_name} not found, will create new one")
            else:
                raise
        
        # Merge with new secrets (new values override existing)
        existing_secrets.update(secrets)
        
        # Update the secret
        client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(existing_secrets, indent=2)
        )
        
        print(f"Successfully updated secret: {secret_name}")
        print(f"Updated {len(secrets)} environment variables")
        
        # Show what was updated (without sensitive values)
        safe_keys = [
            'APP_RELEASE', 'SAGEMAKER_ENDPOINT_NAME', 'OPENAI_EMBEDDING_MODEL', 
            'OPENAI_MODEL', 'PHOENIX_PROJECT_NAME', 'PHOENIX_COLLECTOR_ENDPOINT',
            'WEBHOOK_URL', 'WEBHOOK_USER', 'BASIC_AUTH_USER', 'DEBUGPY_ENABLED',
            'PYDEVD_DISABLE_FILE_VALIDATION', 'ENABLE_PROFILING'
        ]
        
        print("\nUpdated variables:")
        for key in secrets:
            if key in safe_keys:
                print(f"  {key}: {secrets[key]}")
            else:
                print(f"  {key}: [REDACTED]")
                
    except ClientError as e:
        print(f"Error updating secret: {e}")
        sys.exit(1)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate AWS Secrets Manager from .env.local')
    parser.add_argument('--secret-name', default='rag-worker-app-secrets-prod', 
                       help='Name of the AWS secret (default: rag-worker-app-secrets-prod)')
    parser.add_argument('--region', default='eu-central-1',
                       help='AWS region (default: eu-central-1)')
    parser.add_argument('--env-file', default='.env.local',
                       help='Environment file to read (default: .env.local)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without actually updating')
    
    args = parser.parse_args()
    
    # Load environment variables
    secrets = load_env_file(args.env_file)
    
    if not secrets:
        print("No environment variables found to update")
        sys.exit(1)
    
    if args.dry_run:
        print(f"DRY RUN: Would update secret '{args.secret_name}' with:")
        for key, value in secrets.items():
            if key in ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'COHERE_API_KEY', 
                      'SUPABASE_KEY', 'SUPABASE_PASSWORD', 'BASIC_AUTH_ADMIN_PASS',
                      'WEBHOOK_PASS', 'BASIC_AUTH_PASS', 'OTEL_EXPORTER_OTLP_HEADERS',
                      'PHOENIX_CLIENT_HEADERS']:
                print(f"  {key}: [REDACTED]")
            else:
                print(f"  {key}: {value}")
        return
    
    # Update the secret
    update_secret(args.secret_name, secrets, args.region)

if __name__ == '__main__':
    main()