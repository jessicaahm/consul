"""
Configuration loader for Consul-Vault integration.
"""
import os
import yaml
from typing import Dict, Any


class Config:
    """Configuration management for the integration."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration from file and environment variables."""
        self.config_path = config_path
        self._config = self._load_config()
        self._override_from_env()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _override_from_env(self):
        """Override configuration with environment variables."""
        # Vault token from environment
        if os.getenv('VAULT_TOKEN'):
            self._config['vault']['token'] = os.getenv('VAULT_TOKEN')
        
        if os.getenv('VAULT_ADDR'):
            self._config['vault']['address'] = os.getenv('VAULT_ADDR')
        
        # Consul token from environment
        if os.getenv('CONSUL_HTTP_TOKEN'):
            self._config['consul']['token'] = os.getenv('CONSUL_HTTP_TOKEN')
        
        if os.getenv('CONSUL_HTTP_ADDR'):
            addr = os.getenv('CONSUL_HTTP_ADDR')
            if '://' in addr:
                scheme, rest = addr.split('://', 1)
                self._config['consul']['scheme'] = scheme
                if ':' in rest:
                    host, port = rest.rsplit(':', 1)
                    self._config['consul']['host'] = host
                    self._config['consul']['port'] = int(port)
                else:
                    self._config['consul']['host'] = rest
    
    @property
    def vault(self) -> Dict[str, Any]:
        """Get Vault configuration."""
        return self._config.get('vault', {})
    
    @property
    def consul(self) -> Dict[str, Any]:
        """Get Consul configuration."""
        return self._config.get('consul', {})
    
    @property
    def integration(self) -> Dict[str, Any]:
        """Get integration configuration."""
        return self._config.get('integration', {})
