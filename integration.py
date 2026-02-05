"""
Integration layer connecting Consul and Vault for secure secret management.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from vault_client import VaultClient
from consul_client import ConsulClient

logger = logging.getLogger(__name__)


class ConsulVaultIntegration:
    """Integration between Consul and Vault for managing service secrets."""
    
    def __init__(self, vault_client: VaultClient, consul_client: ConsulClient, secret_prefix: str = "consul-services"):
        """
        Initialize the integration.
        
        Args:
            vault_client: Configured VaultClient instance
            consul_client: Configured ConsulClient instance
            secret_prefix: Prefix for secrets in Vault
        """
        self.vault = vault_client
        self.consul = consul_client
        self.secret_prefix = secret_prefix
    
    def store_service_secret(self, service_name: str, secret_data: Dict[str, Any]) -> bool:
        """
        Store service secrets in Vault and reference in Consul.
        
        Args:
            service_name: Name of the service
            secret_data: Dictionary containing secret data
            
        Returns:
            True if successful, False otherwise
        """
        # Store secret in Vault
        vault_path = f"{self.secret_prefix}/{service_name}"
        if not self.vault.write_secret(vault_path, secret_data):
            return False
        
        # Store reference in Consul KV
        reference = {
            "vault_path": vault_path,
            "mount_point": self.vault.mount_point
        }
        consul_key = f"services/{service_name}/vault-secret"
        
        if not self.consul.put_kv(consul_key, json.dumps(reference)):
            logger.error(f"Failed to store Vault reference in Consul for {service_name}")
            return False
        
        logger.info(f"Successfully stored secret for service {service_name}")
        return True
    
    def get_service_secret(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve service secrets from Vault via Consul reference.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Secret data dictionary, or None if not found
        """
        # Get Vault reference from Consul
        consul_key = f"services/{service_name}/vault-secret"
        reference_str = self.consul.get_kv(consul_key)
        
        if not reference_str:
            logger.warning(f"No Vault reference found in Consul for {service_name}")
            return None
        
        try:
            reference = json.loads(reference_str)
            vault_path = reference.get('vault_path')
            
            if not vault_path:
                logger.error(f"Invalid Vault reference for {service_name}")
                return None
            
            # Retrieve secret from Vault using the full path
            secret = self.vault.read_secret(vault_path)
            return secret
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Vault reference for {service_name}: {e}")
            return None
    
    def delete_service_secret(self, service_name: str) -> bool:
        """
        Delete service secrets from both Vault and Consul.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if successful, False otherwise
        """
        success = True
        
        # Delete from Vault
        vault_path = f"{self.secret_prefix}/{service_name}"
        if not self.vault.delete_secret(vault_path):
            logger.warning(f"Failed to delete secret from Vault for {service_name}")
            success = False
        
        # Delete reference from Consul
        consul_key = f"services/{service_name}/vault-secret"
        if not self.consul.delete_kv(consul_key):
            logger.warning(f"Failed to delete Vault reference from Consul for {service_name}")
            success = False
        
        return success
    
    def register_service_with_secrets(self, service_name: str, service_id: str,
                                     address: str, port: int,
                                     secrets: Dict[str, Any],
                                     tags: List[str] = None,
                                     meta: Dict[str, str] = None) -> bool:
        """
        Register a service in Consul and store its secrets in Vault.
        
        Args:
            service_name: Service name
            service_id: Unique service ID
            address: Service address
            port: Service port
            secrets: Dictionary of secrets to store in Vault
            tags: Optional service tags
            meta: Optional service metadata
            
        Returns:
            True if successful, False otherwise
        """
        # Store secrets in Vault first
        if not self.store_service_secret(service_name, secrets):
            logger.error(f"Failed to store secrets for {service_name}")
            return False
        
        # Add metadata indicating secrets are in Vault
        if meta is None:
            meta = {}
        meta['secrets_in_vault'] = 'true'
        
        # Register service with Consul
        if not self.consul.register_service(service_name, service_id, address, port, tags, meta):
            logger.error(f"Failed to register service {service_name}")
            # Attempt to clean up secrets
            self.delete_service_secret(service_name)
            return False
        
        logger.info(f"Successfully registered service {service_name} with secrets in Vault")
        return True
    
    def list_services_with_secrets(self) -> List[str]:
        """
        List all services that have secrets stored in Vault.
        
        Returns:
            List of service names
        """
        try:
            secrets = self.vault.list_secrets(self.secret_prefix)
            return secrets if secrets else []
        except Exception as e:
            logger.error(f"Error listing services with secrets: {e}")
            return []
