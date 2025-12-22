# Python Application
Retrieve a secret via TLS with no hardcoding
- `get_secret()` in [`vault_client.py`](./vault_client.py)

## Test locally
```
export VAULT_TOKEN=<root-token>
python app/main.py
```

## Integration test ([`test_vault.py`](./test_vault.py))
Validates secure, TLS-enabled retrieval of secrets from a live HashiCorp Vault instance during CI, without asserting or exposing secret values, ensuring both correctness and security
- Connects to a Vault instance
- Uses TLS and authentication
- Reads from KV storage

## Secuirty configuration
TLS verification for Vault is configurable via Helm values (`vault.verifyTLS`) and optionally supports a custom CA bundle via `VAULT_CACERT`, following best practices for environment-based security configuration.
