# This script will simulate using vault as the ca provider with consul

# Configure your environment variables
export VAULT_PORT=8200
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN="root"
export DIRECTORY=$(pwd) # Please make sure you are in demo directory
echo "Using directory: $DIRECTORY"
export VAULT_LICENSE="YOUR_VAULT_ENTERPRISE_LICENSE_KEY_HERE" # Replace with your Vault Enterprise license key

# setup vault

echo "1. Setting up Vault Enterprise in Dev Mode"
docker run --name=vault -d \
  -p 8200:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=root \
  -e VAULT_API_ADDR="$VAULT_ADDR" \
  -e VAULT_LICENSE="$VAULT_LICENSE" \
  hashicorp/vault-enterprise

sleep 3

# Configure Vault
echo "2. Configure Vault Approle"
vault policy write connect-ca "$DIRECTORY/setup/vault/vault-policy-connect-ca.hcl"
echo "Read Vault Policies"
vault policy read connect-ca

vault auth enable approle
vault auth tune -max-lease-ttl=730d approle
vault read sys/auth/approle/tune

# Write approle Note: Should be service token
vault write auth/approle/role/my-consul-role \
    token_policies="connect-ca" \
    secret_id_ttl=3m \
    token_ttl=3m \
    token_max_ttl=3m \
    secret_id_num_uses=1 

vault read auth/approle/role/my-consul-role

# Fetch role-id and secret-id
echo "3. Fetch Role ID and Secret ID"
export ROLE_ID=$(vault read auth/approle/role/my-consul-role/role-id -format=json | jq -r .data.role_id)
export SECRET_ID=$(vault write -f auth/approle/role/my-consul-role/secret-id -format=json | jq -r .data.secret_id) 
echo "ROLEID: $ROLE_ID"
echo "SECRETID: $SECRET_ID"

# Write file to consul

echo "4. Writing Consul Configuration File"

# Remove old file
echo "removing old consul file"
rm -f "${DIRECTORY}/setup/consul/server.hcl"

cat <<EOF > "${DIRECTORY}/setup/consul/server.hcl"
ui_config {
  enabled = true
}

## Service mesh CA configuration
connect {
  enabled = true
  ca_provider = "vault"
    ca_config {
        address = "http://host.docker.internal:8200"
        tls_skip_verify = true
        root_pki_path = "connect_root"
        intermediate_pki_path = "connect_dc1_inter"
        leaf_cert_ttl = "1h"
        rotation_period = "2160h"
        intermediate_cert_ttl = "8760h"
        private_key_type = "rsa"
        private_key_bits = 2048
        auth_method {
          type = "approle"
          mount_path = "approle"
          params = {
            role_id   = "$ROLE_ID"
            secret_id = "$SECRET_ID"
          }
        }
    }
}

addresses {
  grpc = "127.0.0.1"
}

ports {
  grpc  = 8502
}
EOF

echo "5. Viewing Consul Configuration File"
cat "${DIRECTORY}/setup/consul/server.hcl"

# Install Consul
echo "6. Starting Consul Server with Vault as CA Provider"
docker network create consul-network

docker run --name=consul-server -d --network=consul-network \
  -v "${DIRECTORY}/setup/consul:/consul/config" \
  -p 8500:8500 \
  -p 8600:8600/udp hashicorp/consul consul agent -server -ui \
  -node=server-1 -bootstrap-expect=1 -client=0.0.0.0 \
  -data-dir=/consul/data \
  -config-dir=/consul/config

sleep 10

# Get config
docker exec consul-server consul connect ca get-config

# Ensure it is using Vault
export PROVDER=$(docker exec consul-server consul connect ca get-config | jq .Provider)
echo "CA Provider is: $PROVDER"

# Ensure Consul is init
curl -s http://localhost:8500/v1/agent/connect/ca/roots

# Requst new certificate
curl -s http://localhost:8500/v1/agent/connect/ca/leaf/newservice

# Test Secret Renewal
export SECRET_ID2=$(vault write -f auth/approle/role/my-consul-role/secret-id -format=json | jq -r .data.secret_id) 
echo $SECRET_ID2
export SECRET_ID2_ACCESSOR=$(vault write -f auth/approle/role/my-consul-role/secret-id -format=json | jq -r .data.secret_id_accessor)

echo "Observe the 2nd Secret_ID expiry"
vault write auth/approle/role/my-consul-role/secret-id-accessor/lookup \
    secret_id_accessor=$SECRET_ID2_ACCESSOR

echo "7. Update Consul Secret_ID. No restart required"

# Update Consul
curl -X PUT http://localhost:8500/v1/connect/ca/configuration \
  -H "Content-Type: application/json" \
  -d '{
    "Provider": "vault",
    "Config": {
      "Address": "http://host.docker.internal:8200",
      "TLSSkipVerify": true,
      "RootPKIPath": "connect_root",
      "IntermediatePKIPath": "connect_dc1_inter",
      "LeafCertTTL": "1h",
      "RotationPeriod": "2160h",
      "IntermediateCertTTL": "8760h",
      "PrivateKeyType": "rsa",
      "PrivateKeyBits": 2048,
      "AuthMethod": {
        "Type": "approle",
        "MountPath": "approle",
        "Params": {
          "role_id": '${ROLE_ID}',
          "secret_id": '${SECRET_ID2}'
        }
      }
    }
  }'

# Request new certificate
curl -s http://localhost:8500/v1/agent/connect/ca/leaf/web | jq .

echo "8. sleep 180s/3mins for the tokens to be expired"
sleep 180

curl -s -verbose \
    http://localhost:8500/v1/agent/connect/ca/leaf/web2 | jq .

curl -s -verbose \
    http://localhost:8500/v1/agent/connect/ca/leaf/web3 | jq .

echo "Look out for the following error: `error issuing cert: Error making API request.`"
echo "Error is expected since approle has expired. This will be the resulting outcome if approle secret_id is not renewed"

# error issuing cert: Error making API request.

# URL: PUT http://host.docker.internal:8200/v1/connect_dc1_inter/sign/leaf-cert
# Code: 403. Errors:

# * 2 errors occurred:
#         * permission denied
#         * invalid token


# observe the behavior in consul logs
# docker logs consul-server 2>&1 | grep -i "vault\|ca\|

# Look out for the following error:

# Cleanup
# docker rm -f $(docker ps -aq) && docker network prune -f