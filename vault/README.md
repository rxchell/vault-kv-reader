# Vault 

## Start Vault locally (with TLS)
### 1. Generate a self-signed cert
Self-signed certificate generated with OpenSSL to enable TLS for Vault
- In production, this would be replaced by a CA-signed certificate
- For CI and local environments, this approach provides encrypted transport and certificate verification

```
openssl req -x509 -newkey rsa:4096 -keyout vault.key -out vault.crt -days 365 -nodes
```
- Generates a new RSA private key
    - A secret, large number used in asymmetric cryptography (Rivest-Shamir-Adleman) for **decrypting** data or creating digital signatures
    - Paired with a public key for encryption
- Generates a new X.509 certificate
- Signs the certificate with its own key (self-signed)
- Outputs:

| File        |   What  | Used by | Purpose               |
| ----------- | ------- | ------- | --------------------- |
| `vault.key` | Private key | Vault   | Decrypt TLS traffic   |
| `vault.crt` | Public Certificate | Clients | Verify Vault identity |

> Note: Command is revised in [Step 5](#5-initialise-vault--store-a-secret-in-vault-kv-store-using-initsh)

**Arguments**
- `openssl`
    - Used for cryptography
    - Certificate generation
    - TLS testing
- `req`
    - Create Certificate Signing Requests (CSRs)
    - Or create self-signed certificates (when combined with `-x509`)
- `-x509`
    - Generate a self-signed X.509 certificate instead of a CSR
        - Act as own Certificate Authority (instead of generate a CSR → send to CA → get cert)
    - Standard format for public key certificates, digital documents that securely associate cryptographic key pairs with identities such as websites, individuals, organisations
- `-newkey rsa:4096`
    - Create a new RSA private key, 4096 bits long
- `-keyout vault.key`
    - Write the private key to `vault.key`
- `-out vault.crt`
    - Write the public certificate to `vault.crt`
- `-days 365`
    - Certificate is valid for 365 days
- `-nodes`
    - “No DES” → do NOT encrypt the private key with a passphrase
    - Vault needs to start automatically
    - No human should type a password at startup

### 2. Vault Configuration in [`vault.hcl`](./vault.hcl)
- `.hcl` file: Uses the HashiCorp Configuration Language (HCL)
- Vault:
    - Uses `vault.key` to decrypt
    - Presents `vault.crt` to clients

### 3. Start the Vault server
```
vault server -config=vault.hcl
```
- Starts Vault using the specified configuration
- Loads TLS certs, storage backend, and UI settings
- Vault now listens securely on HTTPS

### 4. TLS requirement met 
- TLS certificates are generated
- Vault is configured to use TLS
- Plain HTTP is disabled
    - Vault only exposes a TLS-enabled TCP listener.
    Since no listener is configured without TLS, Vault does not accept unencrypted HTTP (`http://`) traffic. 
- All client–server communication is encrypted using TLS
- Vault UI is served over HTTPS

### 5. Initialise Vault & store a secret in Vault KV store using [`init.sh`](./init-vault.sh)
- Client configuration:
    - Trusts the certificate
    - Verifies TLS connection
    - Prevents MITM attacks

**Steps:**
1. Initialise Vault (only once)
    ```
    export VAULT_ADDR=https://127.0.0.1:8200
    ```
    - Set the Vault server address for the CLI

    ```
    export VAULT_CACERT=./tls/vault.crt
    ```
    - Tell the Vault CLI to trust the self-signed certificate

    ```
    vault operator init
    ```
    - Bootstrap Vault for the first time
    - Save the unseal keys and root token securely
    - Vault starts in a sealed state

2. Run [`tls/init-vault.sh`](./init-vault.sh)
    ```
    ./init-vault.sh
    ```
    - Unseal Vault 
    - Login (replace `<root_token>` with actual token from above)
    - Enable KV 
    - Store secret
    
3. Verify that the secret is stored
    ```
    vault kv get kv/store
    ```

> **Sealing / Unsealing:** Vault was initialised using Shamir seal with a threshold of 3 out of 5 unseal keys. The server remained sealed until the required number of unseal operations were performed. Secrets engines could only be enabled after the Vault was fully unsealed, demonstrating correct Vault security behaviour.

#### Problem encountered: TLS hostname / certificate mismatch (common with self-signed certs)
```
2025-12-15T17:33:14.007+0800 [INFO] http: TLS handshake error from 127.0.0.1:62856: remote error: tls: bad certificate
```
- Vault is running
- Client rejects the cert (or Vault rejects the client request) as the certificate does not match the address used

##### Cause
- Certificate was likely generated without Subject Alternative Names (SANs)
- Modern TLS ignores the CN field and requires SANs that match the hostname or IP you connect with (`https://127.0.0.1:8200`)
- Result: TLS handshake fails → bad certificate

##### Fix
Regenerate the certificate with SANs
- Create an [OpenSSL config file](./tls/openssl.cnf)
- Generate a new cert using the config 
    ```
    openssl req -x509 -nodes -days 365 \
    -newkey rsa:4096 \
    -keyout tls/vault.key \
    -out tls/vault.crt \
    -config tls/openssl.cnf
    ```
- Cert is now valid for `localhost` and `127.0.0.1`
- Restart vault ([step 3](#3-start-the-vault-server))