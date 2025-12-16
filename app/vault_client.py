import os
import hvac

def get_secret():
    client = hvac.Client(
        url=os.environ["VAULT_ADDR"],
        token=os.environ["VAULT_TOKEN"],
        verify=os.environ["VAULT_CACERT"]
    )

    secret = client.secrets.kv.v2.read_secret_version(
        path="store",
        mount_point="kv"
    )

    return secret["data"]["data"]["password"]
