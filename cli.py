#!/usr/bin/env python3
"""
Command-line interface for Consul-Vault integration.
"""
import argparse
import logging
import sys
import json
from config_loader import Config
from vault_client import VaultClient
from consul_client import ConsulClient
from integration import ConsulVaultIntegration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_integration(config_path="config.yaml"):
    """Initialize the integration components."""
    config = Config(config_path)
    
    vault_client = VaultClient(
        address=config.vault['address'],
        token=config.vault['token'],
        namespace=config.vault.get('namespace', ''),
        mount_point=config.vault.get('mount_point', 'secret')
    )
    
    if not vault_client.is_authenticated():
        logger.error("Vault authentication failed")
        sys.exit(1)
    
    consul_client = ConsulClient(
        host=config.consul['host'],
        port=config.consul['port'],
        token=config.consul.get('token', ''),
        scheme=config.consul.get('scheme', 'http'),
        datacenter=config.consul.get('datacenter', 'dc1')
    )
    
    integration = ConsulVaultIntegration(
        vault_client=vault_client,
        consul_client=consul_client,
        secret_prefix=config.integration.get('secret_prefix', 'consul-services')
    )
    
    return integration, consul_client


def cmd_register(args):
    """Register a service with secrets."""
    integration, _ = init_integration(args.config)
    
    # Parse secrets from JSON string or file
    if args.secrets_file:
        with open(args.secrets_file, 'r') as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(args.secrets)
    
    # Parse tags and metadata
    tags = args.tags.split(',') if args.tags else []
    meta = json.loads(args.meta) if args.meta else {}
    
    success = integration.register_service_with_secrets(
        service_name=args.name,
        service_id=args.service_id or f"{args.name}-{args.port}",
        address=args.address,
        port=args.port,
        secrets=secrets,
        tags=tags,
        meta=meta
    )
    
    if success:
        logger.info(f"Service {args.name} registered successfully")
    else:
        logger.error(f"Failed to register service {args.name}")
        sys.exit(1)


def cmd_get_secret(args):
    """Get secrets for a service."""
    integration, _ = init_integration(args.config)
    
    secrets = integration.get_service_secret(args.name)
    
    if secrets:
        print(json.dumps(secrets, indent=2))
    else:
        logger.error(f"No secrets found for service {args.name}")
        sys.exit(1)


def cmd_store_secret(args):
    """Store secrets for a service."""
    integration, _ = init_integration(args.config)
    
    # Parse secrets from JSON string or file
    if args.secrets_file:
        with open(args.secrets_file, 'r') as f:
            secrets = json.load(f)
    else:
        secrets = json.loads(args.secrets)
    
    success = integration.store_service_secret(args.name, secrets)
    
    if success:
        logger.info(f"Secrets stored successfully for {args.name}")
    else:
        logger.error(f"Failed to store secrets for {args.name}")
        sys.exit(1)


def cmd_delete_secret(args):
    """Delete secrets for a service."""
    integration, _ = init_integration(args.config)
    
    success = integration.delete_service_secret(args.name)
    
    if success:
        logger.info(f"Secrets deleted successfully for {args.name}")
    else:
        logger.error(f"Failed to delete secrets for {args.name}")
        sys.exit(1)


def cmd_list_services(args):
    """List services with secrets."""
    integration, _ = init_integration(args.config)
    
    services = integration.list_services_with_secrets()
    
    if services:
        print("Services with secrets in Vault:")
        for service in services:
            print(f"  - {service}")
    else:
        print("No services found with secrets in Vault")


def cmd_deregister(args):
    """Deregister a service."""
    _, consul_client = init_integration(args.config)
    
    success = consul_client.deregister_service(args.service_id)
    
    if success:
        logger.info(f"Service {args.service_id} deregistered successfully")
    else:
        logger.error(f"Failed to deregister service {args.service_id}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Consul-Vault Integration CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-c', '--config', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register a service with secrets')
    register_parser.add_argument('name', help='Service name')
    register_parser.add_argument('address', help='Service address')
    register_parser.add_argument('port', type=int, help='Service port')
    register_parser.add_argument('--service-id', help='Service ID (default: name-port)')
    register_parser.add_argument('--secrets', help='Secrets as JSON string')
    register_parser.add_argument('--secrets-file', help='Path to JSON file with secrets')
    register_parser.add_argument('--tags', help='Comma-separated tags')
    register_parser.add_argument('--meta', help='Metadata as JSON string')
    register_parser.set_defaults(func=cmd_register)
    
    # Get secret command
    get_parser = subparsers.add_parser('get-secret', help='Get secrets for a service')
    get_parser.add_argument('name', help='Service name')
    get_parser.set_defaults(func=cmd_get_secret)
    
    # Store secret command
    store_parser = subparsers.add_parser('store-secret', help='Store secrets for a service')
    store_parser.add_argument('name', help='Service name')
    store_parser.add_argument('--secrets', help='Secrets as JSON string')
    store_parser.add_argument('--secrets-file', help='Path to JSON file with secrets')
    store_parser.set_defaults(func=cmd_store_secret)
    
    # Delete secret command
    delete_parser = subparsers.add_parser('delete-secret', help='Delete secrets for a service')
    delete_parser.add_argument('name', help='Service name')
    delete_parser.set_defaults(func=cmd_delete_secret)
    
    # List services command
    list_parser = subparsers.add_parser('list', help='List services with secrets')
    list_parser.set_defaults(func=cmd_list_services)
    
    # Deregister command
    dereg_parser = subparsers.add_parser('deregister', help='Deregister a service')
    dereg_parser.add_argument('service_id', help='Service ID')
    dereg_parser.set_defaults(func=cmd_deregister)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
