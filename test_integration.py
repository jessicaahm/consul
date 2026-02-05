"""
Unit tests for Consul-Vault integration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from config_loader import Config
from vault_client import VaultClient
from consul_client import ConsulClient
from integration import ConsulVaultIntegration
import json


class TestConfig:
    """Tests for configuration loader."""
    
    @patch('config_loader.os.path.exists')
    @patch('builtins.open')
    @patch('config_loader.yaml.safe_load')
    def test_load_config(self, mock_yaml, mock_open, mock_exists):
        """Test configuration loading from file."""
        mock_exists.return_value = True
        mock_yaml.return_value = {
            'vault': {'address': 'http://localhost:8200', 'token': 'test-token'},
            'consul': {'host': 'localhost', 'port': 8500},
            'integration': {'secret_prefix': 'test-prefix'}
        }
        
        config = Config()
        
        assert config.vault['address'] == 'http://localhost:8200'
        assert config.consul['host'] == 'localhost'
        assert config.integration['secret_prefix'] == 'test-prefix'
    
    @patch('config_loader.os.path.exists')
    def test_missing_config_file(self, mock_exists):
        """Test error handling for missing config file."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            Config()


class TestVaultClient:
    """Tests for Vault client wrapper."""
    
    @patch('vault_client.hvac.Client')
    def test_initialization(self, mock_hvac):
        """Test Vault client initialization."""
        client = VaultClient(
            address='http://localhost:8200',
            token='test-token',
            namespace='test-ns',
            mount_point='secret'
        )
        
        assert client.address == 'http://localhost:8200'
        assert client.mount_point == 'secret'
        mock_hvac.assert_called_once()
    
    @patch('vault_client.hvac.Client')
    def test_write_secret(self, mock_hvac):
        """Test writing secrets to Vault."""
        mock_instance = MagicMock()
        mock_hvac.return_value = mock_instance
        
        client = VaultClient('http://localhost:8200', 'test-token')
        result = client.write_secret('test/path', {'key': 'value'})
        
        assert result is True
        mock_instance.secrets.kv.v2.create_or_update_secret.assert_called_once()
    
    @patch('vault_client.hvac.Client')
    def test_read_secret(self, mock_hvac):
        """Test reading secrets from Vault."""
        mock_instance = MagicMock()
        mock_instance.secrets.kv.v2.read_secret_version.return_value = {
            'data': {'data': {'key': 'value'}}
        }
        mock_hvac.return_value = mock_instance
        
        client = VaultClient('http://localhost:8200', 'test-token')
        result = client.read_secret('test/path')
        
        assert result == {'key': 'value'}
    
    @patch('vault_client.hvac.Client')
    def test_delete_secret(self, mock_hvac):
        """Test deleting secrets from Vault."""
        mock_instance = MagicMock()
        mock_hvac.return_value = mock_instance
        
        client = VaultClient('http://localhost:8200', 'test-token')
        result = client.delete_secret('test/path')
        
        assert result is True
        mock_instance.secrets.kv.v2.delete_metadata_and_all_versions.assert_called_once()


class TestConsulClient:
    """Tests for Consul client wrapper."""
    
    @patch('consul_client.consul.Consul')
    def test_initialization(self, mock_consul):
        """Test Consul client initialization."""
        client = ConsulClient(
            host='localhost',
            port=8500,
            token='test-token',
            scheme='http',
            datacenter='dc1'
        )
        
        assert client.host == 'localhost'
        assert client.port == 8500
        mock_consul.assert_called_once()
    
    @patch('consul_client.consul.Consul')
    def test_register_service(self, mock_consul):
        """Test service registration."""
        mock_instance = MagicMock()
        mock_consul.return_value = mock_instance
        
        client = ConsulClient()
        result = client.register_service(
            name='test-service',
            service_id='test-service-1',
            address='127.0.0.1',
            port=8080
        )
        
        assert result is True
        mock_instance.agent.service.register.assert_called_once()
    
    @patch('consul_client.consul.Consul')
    def test_put_kv(self, mock_consul):
        """Test storing key-value pairs."""
        mock_instance = MagicMock()
        mock_consul.return_value = mock_instance
        
        client = ConsulClient()
        result = client.put_kv('test/key', 'test-value')
        
        assert result is True
        mock_instance.kv.put.assert_called_once_with('test/key', 'test-value')
    
    @patch('consul_client.consul.Consul')
    def test_get_kv(self, mock_consul):
        """Test retrieving key-value pairs."""
        mock_instance = MagicMock()
        mock_instance.kv.get.return_value = (None, {'Value': b'test-value'})
        mock_consul.return_value = mock_instance
        
        client = ConsulClient()
        result = client.get_kv('test/key')
        
        assert result == 'test-value'


class TestConsulVaultIntegration:
    """Tests for the integration layer."""
    
    def test_store_service_secret(self):
        """Test storing service secrets."""
        mock_vault = Mock(spec=VaultClient)
        mock_vault.write_secret.return_value = True
        mock_vault.mount_point = 'secret'
        
        mock_consul = Mock(spec=ConsulClient)
        mock_consul.put_kv.return_value = True
        
        integration = ConsulVaultIntegration(mock_vault, mock_consul, 'test-prefix')
        result = integration.store_service_secret('test-service', {'key': 'value'})
        
        assert result is True
        mock_vault.write_secret.assert_called_once()
        mock_consul.put_kv.assert_called_once()
    
    def test_get_service_secret(self):
        """Test retrieving service secrets."""
        mock_vault = Mock(spec=VaultClient)
        mock_vault.read_secret.return_value = {'key': 'value'}
        mock_vault.mount_point = 'secret'
        
        mock_consul = Mock(spec=ConsulClient)
        reference = json.dumps({
            'vault_path': 'test-prefix/test-service',
            'mount_point': 'secret'
        })
        mock_consul.get_kv.return_value = reference
        
        integration = ConsulVaultIntegration(mock_vault, mock_consul, 'test-prefix')
        result = integration.get_service_secret('test-service')
        
        assert result == {'key': 'value'}
    
    def test_register_service_with_secrets(self):
        """Test registering a service with secrets."""
        mock_vault = Mock(spec=VaultClient)
        mock_vault.write_secret.return_value = True
        mock_vault.mount_point = 'secret'
        
        mock_consul = Mock(spec=ConsulClient)
        mock_consul.put_kv.return_value = True
        mock_consul.register_service.return_value = True
        
        integration = ConsulVaultIntegration(mock_vault, mock_consul, 'test-prefix')
        result = integration.register_service_with_secrets(
            service_name='test-service',
            service_id='test-service-1',
            address='127.0.0.1',
            port=8080,
            secrets={'api_key': 'secret123'}
        )
        
        assert result is True
        mock_vault.write_secret.assert_called_once()
        mock_consul.register_service.assert_called_once()
    
    def test_delete_service_secret(self):
        """Test deleting service secrets."""
        mock_vault = Mock(spec=VaultClient)
        mock_vault.delete_secret.return_value = True
        
        mock_consul = Mock(spec=ConsulClient)
        mock_consul.delete_kv.return_value = True
        
        integration = ConsulVaultIntegration(mock_vault, mock_consul, 'test-prefix')
        result = integration.delete_service_secret('test-service')
        
        assert result is True
        mock_vault.delete_secret.assert_called_once()
        mock_consul.delete_kv.assert_called_once()
