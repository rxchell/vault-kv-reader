# HashiCorp Vault: Key/Value Secrets Retreival
Secrets retrieval from the KV store of a HashiCorp Vault instance

## Key concepts
- Transport Layer Security, TLS (previously: Secure Sockets Layer, SSL)

# Developer Guide
## Repository Structure
```
vault-kv-reader/
├── app/
│   ├── main.py
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
│   │   ├── vault.crt
│   │   └── vault.key
│   ├── init-vault.sh
│   └── README.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── requirements.txt
├── Dockerfile
└── README.md
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
3. CI pipeline with Vault + dependency scanning
4. TLS hardening
5. Containerisation
6. Helm + k3d deployment
7. Security & Enhancements

## Set up Python environment 
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
