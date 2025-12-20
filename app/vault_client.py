import os
import hvac

def get_secret():
    verify = False
    
    # VAULT_CACERT is optional to support non-TLS dev environments (e.g. CI)
    if os.environ.get("VAULT_CACERT"):
        verify = os.environ["VAULT_CACERT"]

    client = hvac.Client(
        url=os.environ["VAULT_ADDR"],
        token=os.environ["VAULT_TOKEN"],
        verify=verify
    )

    secret = client.secrets.kv.v2.read_secret_version(
        path="store",
        mount_point="kv"
    )

    return secret["data"]["data"]["password"]
