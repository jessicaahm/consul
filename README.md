# Consul-Vault Integration

A Python-based integration layer that connects HashiCorp Consul and Vault for secure service secret management.

## Overview

This project provides a seamless integration between Consul (service discovery and configuration) and Vault (secrets management). It allows services registered in Consul to securely store and retrieve their secrets from Vault.

## Features

- **Secure Secret Storage**: Store service secrets in Vault with automatic encryption
- **Service Registration**: Register services in Consul with automatic secret management
- **Secret Retrieval**: Retrieve secrets from Vault using Consul service references
- **Configuration Management**: Flexible configuration via YAML files and environment variables
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Architecture

The integration works by:
1. Storing service secrets in Vault's KV secrets engine
2. Storing references to those secrets in Consul's KV store
3. Providing a unified API for service registration and secret management

## Installation

### Prerequisites

- Python 3.7 or higher
- Access to a Consul server (http://localhost:8500 by default)
- Access to a Vault server (http://localhost:8200 by default)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jessicaahm/consul.git
cd consul
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the integration by editing `config.yaml`:
```yaml
vault:
  address: "http://localhost:8200"
  token: ""  # Or set via VAULT_TOKEN environment variable
  namespace: ""
  mount_point: "secret"

consul:
  host: "localhost"
  port: 8500
  scheme: "http"
  token: ""  # Or set via CONSUL_HTTP_TOKEN environment variable
  datacenter: "dc1"

integration:
  secret_prefix: "consul-services"
  sync_interval: 60
```

## Usage

### Basic Example

```python
from config_loader import Config
from vault_client import VaultClient
from consul_client import ConsulClient
from integration import ConsulVaultIntegration

# Load configuration
config = Config()

# Initialize clients
vault_client = VaultClient(
    address=config.vault['address'],
    token=config.vault['token']
)

consul_client = ConsulClient(
    host=config.consul['host'],
    port=config.consul['port']
)

# Create integration
integration = ConsulVaultIntegration(vault_client, consul_client)

# Register a service with secrets
integration.register_service_with_secrets(
    service_name="my-api",
    service_id="my-api-1",
    address="127.0.0.1",
    port=8080,
    secrets={
        "api_key": "secret-key-123",
        "db_password": "secure-password"
    }
)

# Retrieve secrets for a service
secrets = integration.get_service_secret("my-api")
print(secrets)  # {'api_key': 'secret-key-123', 'db_password': 'secure-password'}
```

### Running the Example

```bash
# Set environment variables
export VAULT_TOKEN="your-vault-token"
export CONSUL_HTTP_TOKEN="your-consul-token"  # Optional

# Run the example
python example.py
```

## Components

### VaultClient (`vault_client.py`)
Wrapper for the Vault API providing:
- Secret read/write operations
- Secret deletion
- Secret listing
- Authentication verification

### ConsulClient (`consul_client.py`)
Wrapper for the Consul API providing:
- Service registration/deregistration
- Service discovery
- KV store operations
- Health checks

### ConsulVaultIntegration (`integration.py`)
Main integration layer providing:
- Unified service and secret management
- Automatic secret storage in Vault
- Reference management in Consul
- Complete lifecycle management

### Config (`config_loader.py`)
Configuration management supporting:
- YAML file configuration
- Environment variable overrides
- Flexible configuration options

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest test_integration.py -v

# Run tests with coverage
pytest test_integration.py --cov=. --cov-report=html
```

## Environment Variables

- `VAULT_TOKEN`: Vault authentication token
- `VAULT_ADDR`: Vault server address
- `CONSUL_HTTP_TOKEN`: Consul ACL token
- `CONSUL_HTTP_ADDR`: Consul server address

## Security Considerations

- Store Vault tokens securely (use environment variables, never commit to git)
- Use Consul ACLs in production environments
- Enable TLS for both Consul and Vault in production
- Regularly rotate secrets and tokens
- Follow the principle of least privilege for token permissions

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.