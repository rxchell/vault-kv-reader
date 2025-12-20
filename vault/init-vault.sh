# Set the Vault server address for the CLI
export VAULT_ADDR=https://127.0.0.1:8200

# Tell the Vault CLI to trust the self-signed certificate
export VAULT_CACERT=./tls/vault.crt

echo "==> Checking Vault status"
vault status || true

# Unlock Vault’s encrypted storage
# Enter multiple unseal keys
echo "==> Unsealing Vault"
vault operator unseal
vault operator unseal
vault operator unseal

echo "==> Login to Vault"
# Authenticate as root
# Grants full administrative access
# vault login <root-token>

# Enable the Key-Value (KV) secrets engine
# version 2, supports: versioning, soft deletes, secret history
# mount at path /kv
vault secrets enable -path=kv kv-v2

# Create a secret at path kv/store
# store the key-value pair "example-secret"
vault kv put kv/store password="example-secret"
