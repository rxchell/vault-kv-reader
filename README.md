# HashiCorp Vault: Key/Value Secrets Retreival
Secrets retrieval from the KV store of a HashiCorp Vault instance

## Key concepts
#### Transport Layer Security, TLS (previously: Secure Sockets Layer, SSL)
- The app supports TLS-secured Vault connections via the `VAULT_CACERT` environment variable.
   - In CI, Vault runs in dev mode over HTTP, so TLS verification is intentionally disabled.
   - In production or cluster deployments, TLS is enabled by providing a CA certificate via Kubernetes secrets.

# Developer Guide
## Repository Structure
```
vault-kv-reader/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── main.py
│   ├── README.md
│   ├── vault_client.py
│   └── test_vault.py
├── helm/
│   └── vault-kv/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           └── serviceaccount.yaml
├── vault/
│   ├── vault.hcl
│   ├── tls/
│   │   ├── openssl.cnf
│   │   ├── vault.crt
│   │   └── vault.key
│   ├── init-vault.sh
│   └── README.md
├── .gitignore
├── README.md
├── Dockerfile
└── requirements.txt
```

## Architecture 
```
Developer / CI
   |
   | (TLS)
   v
HashiCorp Vault (KV v2)
   |
   | Secret read
   v
Python App
   |
   | Helm
   v
k3d (lightweight Kubernetes cluster)
```

## Implementation Steps
1. Minimal Vault + local secret retrieval (no CI, no k8s)
   - [Setting up Vault and storing secret](/vault/README.md)
   - [Retrieving secret from Vault by the app](/app/README.md)

2. Automated validation test against live Vault
   - [Integration Test for secret retrieval](/app/test_vault.py)

3. CI pipeline with Vault + dependency scanning
   - [Development CI](.github/workflows/ci.yml)
   - Production CI

4. Containerisation
5. Helm + k3d deployment
6. Security & Enhancements

## Setting up Python environment 
1. Create virtual environment. 
   ```
   python -m venv vaultenv
   ```
2. Activate virtual environment. 
   ```
   source vaultenv/bin/activate
   ```
3. Install necessary packages.
   ```
   pip install requirements.txt
   ```
4. (if required) Generate a new `requirements.txt`file based on the packages installed in the environment
   ```
   pip freeze > requirements.txt
   ```

## CI workflow
By **running Vault as a service container inside GitHub Actions**, the CI pipeline validates:
- App can retrieve secrets from a real HashiCorp Vault instance
- Communication works over HTTP
- Secrets are not hardcoded
- Dependencies are free of known vulnerabilities

Steps:
1. Workflow triggered on every push and pull request 
2. `test` job runs on a Github-hosted Ubuntu VM
3. Spin up a Vault instance
   - A real HashiCorp Vault server is started as a service container in dev mode.
   - Dev mode is used (does not use TLS) as the CI environment is ephemeral and does not require manual unsealing.
   - GitHub Actions starts a Docker container alongside the job
   - `hashicorp/vault:1.15`
      - Official Vault image; version pinned for reproducible builds
   - `VAULT_DEV_ROOT_TOKEN_ID: root`
      - Vault runs in dev mode
      - Unseals vault, creates root token = "root", enables KV engine
   - `VAULT_DEV_LISTEN_ADDRESS`
      - Listens on all interfaces so Github runner can access it
   - `--cap-add=IPC_LOCK`
      - Required by Vault to lock memory (security requirement)
4. Configure Vault access
   - Environment variables injected into all steps 
   - `VAULT_ADDR`: where app connects to Vault 
   - `VAULT_TOKEN`: how the app authenticates to Vault
   - `VAULT_SKIP_VERIFY`: skips TLS cert validation; required later in production if switching to HTTPS with self-signed certs 
5. Checkout code, pull repository into runner
6. Set up python 
7. Install `vault` CLI on the Github Actions runner
   - Troubleshooting
      - `vault` commands failed 
         - GitHub Actions job was running a Vault server container, but the runner VM did not have the Vault CLI installed
         - Solution: Add this step to download and unzip the Vault CLI
      - Unzipping the `vault` CLI failed 
         - `unzip vault_1.15.6_linux_amd64.zip` extracts the binary as `./vault`. But an existing `./vault` already exists in the current working directory.
         - `unzip` tried to prompt to overwrite the existing vault file
         - GitHub Actions runs in non-interactive mode, so the prompt could not be answered. Step exited with code 1.
         - Solution: Force overwrite or extract to a clean temporary directory (e.g. `unzip -o` or `unzip` into `/tmp`) so no prompt occurs
8. Install dependencies 
9. Wait for Vault readiness
   - Poll Vault’s health endpoint to ensure the server is fully initialised before tests run; avoids race conditions and flaky builds
10. Seed a test secret
   - Test-only secret written to the Vault KV v2 store at runtime
   - Secret value is generated dynamically and never committed to source control
11. Run dependency vulnerability scanning
   - Scan python dependencies with `pip-audit` to detect known Common Vulnerabilities and Exposures (CVEs)
12. Run integration tests
   - Validate successful authentication and retrieval without asserting or exposing the secret value

### Vault Authentication in CI 
- Token-based authentication
   - Vault started in dev mode with a predefined root token
   - Token provided to app via environment variables
   - Token exists only in memory; destroyed when CI job completes
- Used in CI: 
   - Vault instance is ephemeral
   - No production secrets used
   - Token is never committed to version control
> In a production environment, this is replaced with `AppRole` or `Kubernetes` authentication. Tokens would be short-lived and scoped to the minimum required permissions.

