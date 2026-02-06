pid_file = "./pidfile"

log_file = "/var/log/vault-agent.log"

vault {
  address = "https://18.140.242.240:8200"
  retry {
    num_retries = 5
  }
}

auto_auth {
  method "aws" {
    mount_path = "auth/aws-subaccount"
    config = {
      type = "iam"
      role = "foobar"
    }
  }

  sink "file" {
    config = {
      path = "/tmp/file-foo"
    }
  }

  sink "file" {
    wrap_ttl = "5m"
    aad_env_var = "TEST_AAD_ENV"
    dh_type = "curve25519"
    dh_path = "/tmp/file-foo-dhpath2"
    config = {
      path = "/tmp/file-bar"
    }
  }
}

cache {
  // An empty cache stanza still enables caching
}

template_config {
  static_secret_render_interval = "10m"
  exit_on_retry_failure = true
  max_connections_per_host = 20
}

template {
  source = "/etc/vault/server.key.ctmpl"
  destination = "/etc/vault/server.key"
}

template {
  source = "/etc/vault/server.crt.ctmpl"
  destination = "/etc/vault/server.crt"
}
