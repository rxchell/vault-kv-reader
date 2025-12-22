import time
from vault_client import get_secret

if __name__ == "__main__":
    secret = get_secret()
    print(secret)

    # Keep container alive for Kubernetes Deployment
    while True:
        time.sleep(60)
