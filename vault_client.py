"""
Vault client wrapper for secret management.
"""
import hvac
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VaultClient:
    """Wrapper for HashiCorp Vault client."""
    
    def __init__(self, address: str, token: str, namespace: str = "", mount_point: str = "secret"):
        """
        Initialize Vault client.
        
        Args:
            address: Vault server address
            token: Vault authentication token
            namespace: Vault namespace (optional)
            mount_point: KV secrets engine mount point
        """
        self.address = address
        self.mount_point = mount_point
        self.client = hvac.Client(
            url=address,
            token=token,
            namespace=namespace if namespace else None
        )
        
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        try:
            return self.client.is_authenticated()
        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            return False
    
    def write_secret(self, path: str, secret: Dict[str, Any]) -> bool:
        """
        Write a secret to Vault.
        
        Args:
            path: Secret path (without mount point)
            secret: Dictionary of secret data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret,
                mount_point=self.mount_point
            )
            logger.info(f"Successfully wrote secret to {path}")
            return True
        except Exception as e:
            logger.error(f"Error writing secret to {path}: {e}")
            return False
    
    def read_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Read a secret from Vault.
        
        Args:
            path: Secret path (without mount point)
            
        Returns:
            Secret data as dictionary, or None if not found
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Error reading secret from {path}: {e}")
            return None
    
    def delete_secret(self, path: str) -> bool:
        """
        Delete a secret from Vault.
        
        Args:
            path: Secret path (without mount point)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=self.mount_point
            )
            logger.info(f"Successfully deleted secret from {path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting secret from {path}: {e}")
            return False
    
    def list_secrets(self, path: str = "") -> Optional[list]:
        """
        List secrets at a given path.
        
        Args:
            path: Path to list secrets from
            
        Returns:
            List of secret names, or None if error
        """
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=self.mount_point
            )
            return response['data']['keys']
        except Exception as e:
            logger.error(f"Error listing secrets from {path}: {e}")
            return None
