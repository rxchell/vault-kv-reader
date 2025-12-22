import os
import hvac

def get_secret():

    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")

    if not vault_addr or not vault_token:
        raise RuntimeError("VAULT_ADDR or VAULT_TOKEN not set")

    # Default: do not verify TLS (dev / CI)
    verify = False

    # Explicit TLS verification toggle
    if os.getenv("VAULT_VERIFY_TLS", "false").lower() == "true":
        verify = True

    # Custom CA bundle (in production) can override boolean verify
    # VAULT_CACERT is optional to support non-TLS dev environments (e.g. CI)
    if os.getenv("VAULT_CACERT"):
        verify = os.environ["VAULT_CACERT"]

    client = hvac.Client(
        url=vault_addr,
        token=vault_token,
        verify=verify
    )

    secret = client.secrets.kv.v2.read_secret_version(
        path="store",
        mount_point="kv"
    )

    return secret["data"]["data"]["password"]
