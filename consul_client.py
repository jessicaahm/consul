"""
Consul client wrapper for service discovery and KV storage.
"""
import consul
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ConsulClient:
    """Wrapper for HashiCorp Consul client."""
    
    def __init__(self, host: str = "localhost", port: int = 8500, 
                 token: str = "", scheme: str = "http", datacenter: str = "dc1"):
        """
        Initialize Consul client.
        
        Args:
            host: Consul server host
            port: Consul server port
            token: Consul ACL token
            scheme: HTTP or HTTPS
            datacenter: Consul datacenter
        """
        self.host = host
        self.port = port
        self.datacenter = datacenter
        self.client = consul.Consul(
            host=host,
            port=port,
            token=token if token else None,
            scheme=scheme
        )
    
    def register_service(self, name: str, service_id: str, address: str, 
                        port: int, tags: List[str] = None, meta: Dict[str, str] = None) -> bool:
        """
        Register a service with Consul.
        
        Args:
            name: Service name
            service_id: Unique service ID
            address: Service address
            port: Service port
            tags: Optional service tags
            meta: Optional service metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.agent.service.register(
                name=name,
                service_id=service_id,
                address=address,
                port=port,
                tags=tags or [],
                meta=meta or {}
            )
            logger.info(f"Successfully registered service {service_id}")
            return True
        except Exception as e:
            logger.error(f"Error registering service {service_id}: {e}")
            return False
    
    def deregister_service(self, service_id: str) -> bool:
        """
        Deregister a service from Consul.
        
        Args:
            service_id: Service ID to deregister
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.agent.service.deregister(service_id)
            logger.info(f"Successfully deregistered service {service_id}")
            return True
        except Exception as e:
            logger.error(f"Error deregistering service {service_id}: {e}")
            return False
    
    def get_services(self) -> Optional[Dict[str, Any]]:
        """
        Get all registered services.
        
        Returns:
            Dictionary of services, or None if error
        """
        try:
            _, services = self.client.agent.services()
            return services
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return None
    
    def get_service(self, service_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get service instances by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of service instances, or None if error
        """
        try:
            _, services = self.client.health.service(service_name, passing=True)
            return services
        except Exception as e:
            logger.error(f"Error getting service {service_name}: {e}")
            return None
    
    def put_kv(self, key: str, value: str) -> bool:
        """
        Store a key-value pair in Consul KV store.
        
        Args:
            key: Key name
            value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.kv.put(key, value)
            logger.info(f"Successfully stored KV: {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing KV {key}: {e}")
            return False
    
    def get_kv(self, key: str) -> Optional[str]:
        """
        Get a value from Consul KV store.
        
        Args:
            key: Key name
            
        Returns:
            Value as string, or None if not found
        """
        try:
            _, data = self.client.kv.get(key)
            if data:
                return data['Value'].decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Error getting KV {key}: {e}")
            return None
    
    def delete_kv(self, key: str) -> bool:
        """
        Delete a key from Consul KV store.
        
        Args:
            key: Key name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.kv.delete(key)
            logger.info(f"Successfully deleted KV: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting KV {key}: {e}")
            return False
