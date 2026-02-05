# Consul-Vault Integration Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   CLI Tool   │  │  Example App │  │  Your Service│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│                    Integration Layer                         │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │      ConsulVaultIntegration (integration.py)          │ │
│  │                                                        │ │
│  │  • register_service_with_secrets()                    │ │
│  │  • get_service_secret()                               │ │
│  │  • store_service_secret()                             │ │
│  │  • delete_service_secret()                            │ │
│  │  • list_services_with_secrets()                       │ │
│  └─────────────┬──────────────────────┬───────────────────┘ │
└────────────────┼──────────────────────┼─────────────────────┘
                 │                      │
        ┌────────┴────────┐    ┌───────┴────────┐
        │                 │    │                 │
┌───────▼──────────┐ ┌────▼──────────────┐      │
│   VaultClient    │ │  ConsulClient     │      │
│ (vault_client.py)│ │(consul_client.py) │      │
│                  │ │                   │      │
│ • write_secret() │ │ • register_svc()  │      │
│ • read_secret()  │ │ • get_services()  │      │
│ • delete_secret()│ │ • put_kv()        │      │
│ • list_secrets() │ │ • get_kv()        │      │
└────────┬─────────┘ └─────┬─────────────┘      │
         │                 │                    │
         │                 │                    │
┌────────▼─────────────────▼────────────────────▼──────────┐
│            External Services (HashiCorp)                  │
│                                                           │
│  ┌──────────────────┐         ┌──────────────────┐      │
│  │  Vault Server    │         │  Consul Server   │      │
│  │  Port: 8200      │         │  Port: 8500      │      │
│  │                  │         │                  │      │
│  │  Secrets Storage │         │  Service Catalog │      │
│  │  KV v2 Engine    │         │  KV Store        │      │
│  └──────────────────┘         └──────────────────┘      │
└───────────────────────────────────────────────────────────┘
```

## Data Flow

### Registering a Service with Secrets

```
1. Application calls integration.register_service_with_secrets()
   ↓
2. Integration Layer stores secrets in Vault
   POST /v1/secret/data/consul-services/{service_name}
   ↓
3. Integration Layer stores reference in Consul KV
   PUT /v1/kv/services/{service_name}/vault-secret
   {
     "vault_path": "consul-services/{service_name}",
     "mount_point": "secret"
   }
   ↓
4. Integration Layer registers service in Consul
   PUT /v1/agent/service/register
   {
     "name": "{service_name}",
     "address": "...",
     "meta": {"secrets_in_vault": "true"}
   }
   ↓
5. Returns success/failure to application
```

### Retrieving Service Secrets

```
1. Application calls integration.get_service_secret(service_name)
   ↓
2. Integration retrieves reference from Consul KV
   GET /v1/kv/services/{service_name}/vault-secret
   ↓
3. Parse JSON reference to get vault_path
   ↓
4. Integration retrieves secret from Vault
   GET /v1/secret/data/{vault_path}
   ↓
5. Returns decrypted secret data to application
```

## Configuration Flow

```
config.yaml
    ↓
Config Loader (config_loader.py)
    ↓
Environment Variables Override
    ↓
┌──────────────────────────────┐
│  Configuration Object        │
│  • vault.address            │
│  • vault.token              │
│  • consul.host              │
│  • consul.port              │
│  • integration.secret_prefix│
└──────────────────────────────┘
    ↓
Passed to Client Constructors
```

## Security Architecture

```
┌─────────────────────────────────────────────────┐
│            Security Layers                      │
├─────────────────────────────────────────────────┤
│ 1. Authentication                               │
│    • Vault Token (VAULT_TOKEN)                 │
│    • Consul ACL Token (CONSUL_HTTP_TOKEN)      │
├─────────────────────────────────────────────────┤
│ 2. Transport Security                          │
│    • TLS Support (configurable)                │
│    • HTTPS/HTTP schemes                        │
├─────────────────────────────────────────────────┤
│ 3. Secret Storage                              │
│    • Vault encryption at rest                  │
│    • No secrets in Consul (only references)    │
├─────────────────────────────────────────────────┤
│ 4. Access Control                              │
│    • Vault policies                            │
│    • Consul ACLs                               │
├─────────────────────────────────────────────────┤
│ 5. Audit & Logging                             │
│    • Python logging framework                  │
│    • No secrets in logs                        │
└─────────────────────────────────────────────────┘
```

## Component Responsibilities

### VaultClient
- Handles all Vault API communication
- Manages secret CRUD operations
- Uses KV v2 secrets engine
- Validates authentication

### ConsulClient
- Handles all Consul API communication
- Service registration/discovery
- KV store operations
- Health check integration

### ConsulVaultIntegration
- Orchestrates Vault and Consul operations
- Maintains consistency between systems
- Provides unified API
- Handles error scenarios

### Config
- Loads configuration from YAML
- Applies environment overrides
- Validates settings
- Provides structured access

## Development Environment

```
┌────────────────────────────────────┐
│      Docker Compose Setup          │
│                                    │
│  ┌──────────────┐  ┌──────────────┐│
│  │   Vault      │  │   Consul     ││
│  │   Container  │  │   Container  ││
│  │              │  │              ││
│  │   Dev Mode   │  │   Dev Mode   ││
│  │   Token:     │  │   UI Enabled ││
│  │   dev-root-  │  │              ││
│  │   token      │  │              ││
│  └──────────────┘  └──────────────┘│
│        ↑                  ↑         │
│        └──────────────────┘         │
│        Network: consul-vault-       │
│                 network             │
└────────────────────────────────────┘
         ↑
         │
┌────────┴──────────────────────────┐
│   Local Development Machine        │
│                                    │
│   • Python 3.7+                   │
│   • pip install -r requirements   │
│   • pytest for testing            │
│   • CLI tool for manual testing   │
└────────────────────────────────────┘
```

## File Structure

```
consul/
├── config.yaml              # Configuration file
├── config_loader.py         # Config management
├── vault_client.py          # Vault API wrapper
├── consul_client.py         # Consul API wrapper
├── integration.py           # Main integration layer
├── cli.py                   # Command-line interface
├── example.py               # Usage example
├── test_integration.py      # Unit tests
├── setup.py                 # Package setup
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── docker-compose.yaml      # Dev environment
├── Makefile                 # Common tasks
├── example-secrets.json     # Example secrets
├── .gitignore              # Git ignore rules
├── LICENSE                  # MIT License
├── README.md               # Main documentation
├── DEVELOPMENT.md          # Dev guide
├── SUMMARY.md              # Project summary
└── ARCHITECTURE.md         # This file
```

## API Reference

### Integration API

```python
# Create integration instance
integration = ConsulVaultIntegration(vault_client, consul_client)

# Register service with secrets
integration.register_service_with_secrets(
    service_name="api",
    service_id="api-1",
    address="127.0.0.1",
    port=8080,
    secrets={"key": "value"}
)

# Get secrets
secrets = integration.get_service_secret("api")

# Store secrets
integration.store_service_secret("api", {"key": "value"})

# Delete secrets
integration.delete_service_secret("api")

# List services
services = integration.list_services_with_secrets()
```

## Testing Strategy

```
Unit Tests (test_integration.py)
    │
    ├── Config Tests
    │   ├── Load from YAML
    │   ├── Environment overrides
    │   └── Missing file handling
    │
    ├── VaultClient Tests
    │   ├── Initialization
    │   ├── Write secret
    │   ├── Read secret
    │   └── Delete secret
    │
    ├── ConsulClient Tests
    │   ├── Initialization
    │   ├── Register service
    │   ├── Put KV
    │   └── Get KV
    │
    └── Integration Tests
        ├── Store service secret
        ├── Get service secret
        ├── Register with secrets
        └── Delete service secret

All tests use mocking (unittest.mock)
No external dependencies required
```
