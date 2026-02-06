# validate: (1) there should be no errors when consul is updated at step 7
docker logs consul-server -f | grep -i "connect.ca.vault"



# Look out for 2026-02-06T03:04:29.268Z [ERROR] connect.ca.vault: Error renewing token for Vault provider:...