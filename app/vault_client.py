import os
import hvac
import urllib3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Suppress TLS warnings for dev environments
if os.getenv("VAULT_VERIFY_TLS", "false").lower() != "true":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_secret():
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")

    if not vault_addr or not vault_token:
        raise RuntimeError("VAULT_ADDR or VAULT_TOKEN not set")

    # Determine TLS verification
    # Default: do not verify TLS (dev / CI)
    verify = False

    # Explicit TLS verification toggle
    if os.getenv("VAULT_VERIFY_TLS", "false").lower() == "true":
        verify = True

    # Custom CA bundle (in production) can override boolean verify
    # VAULT_CACERT is optional to support non-TLS dev environments (e.g. CI)
    if os.getenv("VAULT_CACERT"):
        verify = os.environ["VAULT_CACERT"]

    logging.info(f"Connecting to Vault at {vault_addr} (TLS verify: {verify})")

    client = hvac.Client(
        url=vault_addr,
        token=vault_token,
        verify=verify
    )

    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed. Check VAULT_TOKEN.")

    try:
        secret_response = client.secrets.kv.v2.read_secret_version(
            path="store",
            mount_point="kv"
        )
        secret = secret_response["data"]["data"]["password"]
        logging.info("Successfully retrieved secret.")
        return secret
    except hvac.exceptions.InvalidPath:
        logging.error("Secret path 'kv/store' not found in Vault.")
        return None
    except KeyError:
        logging.error("Expected key 'password' not found in secret data.")
        return None