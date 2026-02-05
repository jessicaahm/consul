# Consul-Vault Integration Development Guide

## Quick Start with Docker

This guide helps you quickly set up Consul and Vault for development and testing.

### Prerequisites

- Docker and Docker Compose installed
- Python 3.7 or higher

### Setup Development Environment

1. Start Consul and Vault services:
```bash
docker-compose up -d
```

2. Wait for services to be healthy:
```bash
docker-compose ps
```

3. Configure environment variables:
```bash
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-root-token"
export CONSUL_HTTP_ADDR="http://localhost:8500"
```

4. Install the package in development mode:
```bash
pip install -e .
```

### Testing the Integration

1. Run the example script:
```bash
python example.py
```

2. Use the CLI tool:
```bash
# Register a service with secrets
python cli.py register my-api 127.0.0.1 8080 \
  --secrets '{"api_key": "secret123", "db_pass": "dbsecret456"}'

# Get secrets for a service
python cli.py get-secret my-api

# List all services with secrets
python cli.py list

# Delete secrets
python cli.py delete-secret my-api
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest test_integration.py -v

# Run with coverage
pytest test_integration.py --cov=. --cov-report=html
```

### Accessing Service UIs

- **Consul UI**: http://localhost:8500/ui
- **Vault UI**: http://localhost:8200/ui (Token: `dev-root-token`)

### Cleanup

Stop and remove containers:
```bash
docker-compose down
```

## Development Workflow

1. Make code changes
2. Run tests: `pytest test_integration.py`
3. Test manually with docker-compose environment
4. Update documentation if needed
5. Commit changes

## Project Structure

```
.
├── cli.py                  # Command-line interface
├── config.yaml            # Configuration file
├── config_loader.py       # Configuration management
├── consul_client.py       # Consul client wrapper
├── vault_client.py        # Vault client wrapper
├── integration.py         # Integration layer
├── example.py            # Usage example
├── test_integration.py   # Unit tests
├── setup.py              # Package setup
├── docker-compose.yaml   # Dev environment
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
└── README.md             # Main documentation
```

## Architecture

```
┌─────────────────────┐
│   Application       │
│   (Your Service)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Integration Layer  │
│  (integration.py)   │
└─────┬─────────┬─────┘
      │         │
      ▼         ▼
┌─────────┐ ┌──────────┐
│  Vault  │ │  Consul  │
│ Client  │ │  Client  │
└─────────┘ └──────────┘
      │         │
      ▼         ▼
┌─────────┐ ┌──────────┐
│  Vault  │ │  Consul  │
│ Server  │ │  Server  │
└─────────┘ └──────────┘
```

## Common Operations

### Store Service Secrets

```python
integration.store_service_secret(
    service_name="my-service",
    secret_data={
        "api_key": "secret-key",
        "password": "secure-password"
    }
)
```

### Retrieve Service Secrets

```python
secrets = integration.get_service_secret("my-service")
api_key = secrets["api_key"]
```

### Register Service with Secrets

```python
integration.register_service_with_secrets(
    service_name="my-api",
    service_id="my-api-1",
    address="127.0.0.1",
    port=8080,
    secrets={"api_key": "secret"},
    tags=["api", "v1"],
    meta={"version": "1.0.0"}
)
```

## Troubleshooting

### Vault Connection Issues

```bash
# Check Vault status
docker-compose logs vault

# Verify Vault is accessible
curl http://localhost:8200/v1/sys/health
```

### Consul Connection Issues

```bash
# Check Consul status
docker-compose logs consul

# Verify Consul is accessible
curl http://localhost:8500/v1/status/leader
```

### Authentication Issues

- Ensure `VAULT_TOKEN` is set correctly
- Verify token has required permissions
- Check Consul ACL token if ACLs are enabled

## Best Practices

1. **Never commit secrets** - Use environment variables
2. **Use separate tokens** - Development vs Production
3. **Enable TLS** - In production environments
4. **Rotate secrets regularly** - Implement secret rotation
5. **Monitor access** - Enable audit logging
6. **Use namespaces** - For multi-tenant environments
7. **Test thoroughly** - Before deploying to production
