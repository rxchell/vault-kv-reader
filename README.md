# HashiCorp Vault: Key/Value Secrets Retreival
Secrets retrieval from the KV store of a HashiCorp Vault instance

## Key concepts
#### Transport Layer Security, TLS (previously: Secure Sockets Layer, SSL)
- The app supports TLS-secured Vault connections via the `VAULT_CACERT` environment variable.
   - In CI, Vault runs in dev mode over HTTP, so TLS verification is intentionally disabled.
   - In production or cluster deployments, TLS is enabled by providing a CA certificate via Kubernetes secrets.

---

# Developer Guide
1. [Repository Structure](#repository-structure)
2. [Architecture](#architecture)
3. [Implementation Steps](#implementation-steps)
4. [Setting up Python environment](#setting-up-python-environment)
5. [CI workflow](#ci-workflow)
6. [Containerisation](#containerisation)
7. [k3d cluster](#k3d-cluster)
8. [Deployment with Helm](#deployment-with-helm)
9. [Integrate k3d and Helm into CI](#integrate-k3d-and-helm-into-ci)
10. [Dependency Security Handling](#dependency-security-handling)

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
│           └── deployment.yaml
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
1. Set up Vault and local secret retrieval
   - [Setting up Vault and storing secret](/vault/README.md)
   - [Retrieving secret from Vault by the app](/app/README.md)

2. Validation test against live Vault
   - [Integration Test for secret retrieval](/app/test_vault.py)

3. CI pipeline with Vault and dependency scanning
   - [Development CI](.github/workflows/ci.yml)
   - Production CI not implemented

4. [Containerisation](#containerisation)
   - [Dockerfile](./Dockerfile)

5. [Kubernetes cluster (k3d)](#k3d-cluster)

6. [Deployment with Helm](#deployment-with-helm)
   - [Helm files](./helm/vault-kv/)

7. [Integrate k3d and Helm into CI](#integrate-k3d-and-helm-into-ci)

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

---

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

---
## Containerisation
- Packages the app and everything it needs to run into a single, reproducible unit (container image)
   - Includes Python runtime, app code, Vault client library, Python dependencies
- App can run the same way locally, in CI, in Kubernetes 
- Secrets and Vault credentials are explicitly excluded from the image 
   - Instead injected at runtime via environment variables and Kubernetes Secrets
   - Allows container to securely connect over TLS to a Vault instance running outside the cluster
   - Maintains immutability, reproducibility, strong security boundaries

### Importance of containerisation
| Aspect             | Why containerisation is needed          |
| ------------------ | --------------------------------------- |
| Helm deployment    | Helm deploys containers, not raw Python |
| k3d cluster        | Kubernetes runs container images        |
| CI reproducibility | CI runners are ephemeral                |
| External Vault     | Container networking must be controlled |
| Security           | Smaller attack surface                  |

### How containerisation works 
```
Dockerfile
   ↓
docker build
   ↓
Container Image
   ↓
docker run / Kubernetes Pod
   ↓
Python app executes
```

### [Dockerfile](./Dockerfile)
- `FROM python:3.11-slim`
   - Uses a minimal Linux image
   - Comes with Python pre-installed
   - `slim` reduces image size and attack surface
- `WORKDIR /app`
   - All future commands run relative to `/app`
- `COPY requirements.txt .`
   - Enables Docker layer caching
   - Dependencies do not reinstall if code changes
   - Faster rebuilds in CI
- `RUN pip install --no-cache-dir -r requirements.txt`
   - Installs `hvac` (Vault client) and any other dependencies
   - `--no-cache-dir` reduces image size, avoids leftover build artifacts
- `COPY app/ .`
   - Copies `main.py` and `vault_client.py` into container filesystem
- `CMD ["python", "main.py"]`
   - When container starts, Kubernetes executes the default command `python main.py`

### `docker build`
```
docker build -t vault-kv-reader .
```
- Tags the image with the name `vault-kv-reader`
- `.` is the build context; Docker can access all files in current directory and copy them into the image

---

## k3d cluster 
- `k3d` runs a Kubernetes cluster inside Docker containers using k3s (a lightweight Kubernetes distribution).
- Inside each Docker container:
   - `kube-apiserver` handles API requests
   - `kube-scheduler` schedules pods
   - `kubelet` runs containers
   - `containerd` runs the images

### Creating the k3d cluster 
1. Install `k3d`
   ```
   brew install k3d
   ```
2. Create the k3d cluster
   ```
   k3d cluster create vault-kv
   ```
   - Creates a Kubernetes control plane and one worker node, inside Docker containers
3. Verify
   ```
   kubectl get nodes
   ```
4. The Kubernetes cluster is running locally.

### Networking: how the app reaches Vault outside the cluster
- `host.k3d.internal` resolves the problem where
   - App runs inside Kubernetes and Docker containers
   - Vault runs on the host, outside Kubernetes
- `k3d` provides a special DNS name
   ```
   VAULT_ADDR: https://host.k3d.internal:8200
   ```
   - Resolves to: **Pod → Node → Docker → Host → Vault**
- Flow
   ```
   Python app
   ↓
   Kubernetes Pod
   ↓
   k3d container
   ↓
   Docker network bridge
   ↓
   Host machine
   ↓
   Vault
   ```
- Allows the app to retrieve the secret from the same Vault instance outside the cluster

### How secrets are handled inside `k3d`
- Kubernetes Secrets
- Create 
   ```
   kubectl create secret generic vault-token \
   --from-literal=token=<vault-token>
   ```
- Inside the Pod
   - Kubernetes injects the token as an env var
   - Token exists only in memory
   ```
   env:
   -  name: VAULT_TOKEN
      valueFrom:
         secretKeyRef:
            name: vault-token
            key: token
   ```

### Runtime flow inside k3d
1. `k3d` starts cluster (Docker containers)
2. Kubernetes API becomes available
3. Helm deploys app
4. Pod is scheduled to a `k3d` node
5. Node pulls container image
6. Kubernetes injects environment variables
7. Container starts
8. `python main.py` runs
9. App connects to Vault over TLS
10. Secret is retrieved

---

## Deployment with Helm
- For deploying already-working containers into Kubernetes
- Template engine and release manager for Kubernetes
   - Takes templates ([`deployment.yaml`](./helm/vault-kv/templates/deployment.yaml))
      - Runs the container
      - Injects:
         - Vault address (from Helm values)
         - Vault token (from Kubernetes Secret)
      - Keeps secrets out of Git, Docker image, Helm values
   - Fills in values ([`values.yaml`](./helm/vault-kv/values.yaml))
   - Sends real Kubernetes YAML to the cluster
      - Without Helm:
         ```
         image: vault-kv-reader:latest
         VAULT_ADDR: https://host.k3d.internal:8200
         ```
      - With Helm:
         ```
         image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
         VAULT_ADDR: {{ .Values.vault.addr }}
         ```
- Benefits:
   - Change config without rewriting YAML
   - Deploy same app to: local `k3d`, CI, production (hypothetically)

### How Helm deploys the app 
- Helm never runs the app (done by Kubernetes)
```
helm install vault-kv-demo helm/vault-kv-demo
   ↓
Helm renders templates
   ↓
Kubernetes Deployment created
   ↓
Pod pulls Docker image
   ↓
Env vars injected
   ↓
python main.py runs
```

---
## Integrate k3d and Helm into CI
### Steps
1. Ensure Vault is running (outside `k3d`)
   - Skip TLS verification (for local and CI) 
      ```
      export VAULT_ADDR=https://127.0.0.1:8200
      export VAULT_SKIP_VERIFY=true
      ```
      - Resolves the problem of `tls: failed to verify certificate: x509: certificate signed by unknown authority`
         - Vault is running with TLS enabled, using a self-signed certificate.
         - macOS and Vault CLI do not trust self-signed certs by default.
         - When Vault CLI tries to talk to `https://127.0.0.1:8200`, it refuses.
   - To run vault after initialising, refer to step 2 onwards in [Vault documentation](./vault/README.md#start-vault-locally-with-tls)
   - Verify that the vault is running
      ```
      vault status
      ```
      - Process running: Vault binary is up
      - `Initialized: true`: Master key and unseal keys exist; Storage backend is ready
      - `Sealed: false`: Encryption barrier is open, Vault can read and write secrets

2. Create Kubernetes Secret for Vault token
   ```
   kubectl create secret generic vault-token \
   --from-literal=token="$VAULT_TOKEN"
   ```
   - Use Kubernetes Secret as Kubernetes cannot read the shell environment
   - Vault token → Kubernetes Secret → Pod env var
   - Inside Kubernetes, this becomes
      ```
      apiVersion: v1
      kind: Secret
      data:
      token: <base64>
      ```
   - Helm chart later does
      ```
      env:
      - name: VAULT_TOKEN
         valueFrom:
            secretKeyRef:
            name: vault-token
            key: token
      ```

3. Build Docker image
   ```
   docker build -t vault-kv-reader:local .
   ```
   - Kubernetes does not build images
   - The cluster needs a runnable container
   - Image tag is `local`: Don’t push to registry

4. Import image into `k3d`
   ```
   k3d image import vault-kv-reader:local -c vault-kv
   ```
   - `k3d` runs Kubernetes inside Docker
   - Local Docker image (`docker images`) and `k3d` nodes (`docker ps`) are different Docker environments.
   - Command copies the image and injects it into every `k3d` node
   - Without this → `ImagePullBackOff`

5. Deploy with Helm
   ```
   helm install vault-kv-reader helm/vault-kv \
   --set image.repository=vault-kv-reader \
   --set image.tag=local \
   --set vault.addr=https://host.k3d.internal:8200
   ```
   - Helm:
      - Reads `values.yaml`
      - Applies `--set` overrides
      - Renders templates → Kubernetes YAML
      - Sends YAML to Kubernetes API
   - Inside a pod:
      - `localhost` = the container itself 
      - `host.k3d.internal` = laptop ✅
   - This is a k3d DNS bridge
   - TLS verification is configurable via Helm values in `values.yaml`
      ```yaml
         vault:
         verifyTLS: false
      ```
      - This value is passed as the `VAULT_VERIFY_TLS` environment variable to the container.
         - `true` → full certificate verification
         - `false` → skip verification (CI / local dev only)

6a. Verify deployment
   ```
   kubectl get pods
   kubectl logs deployment/vault-kv-reader
   ```

6b. Troubleshooting 
   - Get logs with 
      ```
      kubectl logs pod/vault-kv-reader-<some-id>
      ```
      - `vault-kv-reader-<some-id>` is obtained from `kubectl get pods`
   - `CrashLoopBackOff` status
      - Cause: The app starts, reads secret from Vault, prints `example-secret`, and exits. When a container’s main process exits, Kubernetes interprets that as a crash.Since the deployment expects a long-running pod, Kubernetes restarts it, causing `CrashLoopBackOff`
      - Solution: Keep the app alive. Modify the Python app to stay running after reading the secret.
   - `InsecureRequestWarning: Unverified HTTPS request`
      - Vault is using HTTPS. App is skipping cert verification (`verify=False`). This is acceptable for local dev / CI

6c. If code changed from troubleshooting above, 
   - Step 3: `docker build -t vault-kv-reader:local .`
   - Step 4: `k3d image import vault-kv-reader:local -c vault-kv`
   - Redeploy with helm
      ```
      helm upgrade vault-kv-reader helm/vault-kv \
      --set image.repository=vault-kv-reader \
      --set image.tag=local      
      ```
   - Verify deployment 
      ```
      kubectl get pods
      ```

## Dependency Security Handling
Dependency vulnerability scanning is enforced in the CI pipeline using `pip-audit`.
- The pipeline is configured to fail when known vulnerabilities are detected, ensuring insecure builds are blocked early.
- During development, a vulnerability (CVE-2026-21441) was detected in `urllib3`. The dependency was upgraded to a patched version to remediate the issue, after which the pipeline passed successfully.