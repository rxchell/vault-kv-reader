# Enable HTTPS listener for Vault
# Defines a TCP listener on port 8200 (Vault’s default)

listener "tcp" {
  address       = "0.0.0.0:8200"   # 0.0.0.0 → Vault listens on all network interfaces
  tls_cert_file = "tls/vault.crt"     # points vault to TLS certificate
  tls_key_file  = "tls/vault.key"     # points vault to Private key
}


# File-based storage (for local development)
# Uses the file storage backend
# Stores Vault data (keys, secrets metadata) on disk in ./data
# For Vault to persist data

storage "file" {
  path = "./data"
}


# Enable the Vault web UI
# Accessible via https://<host>:8200/ui
# Ensures encrypted browser-based interaction

ui = true
