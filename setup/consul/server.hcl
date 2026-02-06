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
            role_id   = "7a6facc0-e866-efe7-c1ef-bb966a9d8cd7"
            secret_id = "e8eea0f8-375f-6e72-1c2e-6462542e707e"
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
