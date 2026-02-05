"""
Example usage of Consul-Vault integration.
"""
import logging
import sys
from config_loader import Config
from vault_client import VaultClient
from consul_client import ConsulClient
from integration import ConsulVaultIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main example function demonstrating the integration."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = Config()
        
        # Initialize Vault client
        logger.info("Initializing Vault client...")
        vault_client = VaultClient(
            address=config.vault['address'],
            token=config.vault['token'],
            namespace=config.vault.get('namespace', ''),
            mount_point=config.vault.get('mount_point', 'secret')
        )
        
        # Check Vault authentication
        if not vault_client.is_authenticated():
            logger.error("Vault authentication failed. Please check your token.")
            return 1
        logger.info("Vault authentication successful")
        
        # Initialize Consul client
        logger.info("Initializing Consul client...")
        consul_client = ConsulClient(
            host=config.consul['host'],
            port=config.consul['port'],
            token=config.consul.get('token', ''),
            scheme=config.consul.get('scheme', 'http'),
            datacenter=config.consul.get('datacenter', 'dc1')
        )
        
        # Initialize integration
        logger.info("Initializing Consul-Vault integration...")
        integration = ConsulVaultIntegration(
            vault_client=vault_client,
            consul_client=consul_client,
            secret_prefix=config.integration.get('secret_prefix', 'consul-services')
        )
        
        # Example: Register a service with secrets
        logger.info("Registering example service with secrets...")
        service_name = "example-api"
        service_id = "example-api-1"
        secrets = {
            "api_key": "super-secret-key-12345",
            "db_password": "secure-db-password",
            "jwt_secret": "jwt-signing-secret"
        }
        
        success = integration.register_service_with_secrets(
            service_name=service_name,
            service_id=service_id,
            address="127.0.0.1",
            port=8080,
            secrets=secrets,
            tags=["api", "example"],
            meta={"version": "1.0.0"}
        )
        
        if success:
            logger.info(f"Service {service_name} registered successfully")
        else:
            logger.error(f"Failed to register service {service_name}")
            return 1
        
        # Example: Retrieve secrets for the service
        logger.info(f"Retrieving secrets for {service_name}...")
        retrieved_secrets = integration.get_service_secret(service_name)
        
        if retrieved_secrets:
            logger.info(f"Successfully retrieved secrets for {service_name}")
            logger.info(f"Secret keys: {list(retrieved_secrets.keys())}")
        else:
            logger.error(f"Failed to retrieve secrets for {service_name}")
            return 1
        
        # Example: List all services with secrets
        logger.info("Listing all services with secrets...")
        services = integration.list_services_with_secrets()
        logger.info(f"Services with secrets in Vault: {services}")
        
        # Example: Deregister service (cleanup)
        logger.info(f"Deregistering service {service_id}...")
        consul_client.deregister_service(service_id)
        
        # Note: In production, you might want to keep the secrets in Vault
        # even after deregistering the service. Here we clean up for the example.
        logger.info(f"Cleaning up secrets for {service_name}...")
        integration.delete_service_secret(service_name)
        
        logger.info("Example completed successfully!")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
