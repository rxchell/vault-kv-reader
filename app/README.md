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