path "sys/mounts/connect_root" {
  capabilities = [ "create", "read", "update", "delete", "list" ]
}

path "sys/mounts/connect_dc1_inter" {
  capabilities = [ "create", "read", "update", "delete", "list" ]
}

path "sys/mounts/connect_dc1_inter/tune" {
  capabilities = [ "update" ]
}

path "connect_root/*" {
  capabilities = [ "create", "read", "update", "delete", "list" ]
}

path "connect_dc1_inter/*" {
  capabilities = [ "create", "read", "update", "delete", "list" ]
}

path "auth/token/renew-self" {
  capabilities = [ "update" ]
}

path "auth/token/lookup-self" {
  capabilities = [ "read" ]
}
