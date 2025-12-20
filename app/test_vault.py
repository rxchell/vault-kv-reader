from vault_client import get_secret

def test_secret_retrieval():
    secret=get_secret()
    assert isinstance(secret, str)
    assert secret.strip() != ""