from cryptography.fernet import Fernet
from credentials.local import LocalCredentialStore
from models import Credentials
import pytest


def test_store_credential_with_fernet(tmp_path):

    key = Fernet.generate_key()
    store = LocalCredentialStore(path=tmp_path / "creds.json", fernet_key=key)

    store.store(
        "integration_123",
        Credentials(
            client_id =  "Client1",
            client_secret = "Secret",
        )
    )

    credential = store.get("integration_123")
    assert credential.client_id ==  'Client1'

def test_store_get_when_not_exists(tmp_path):
    key = Fernet.generate_key()
    store = LocalCredentialStore(path=tmp_path / "creds.json", fernet_key=key)

    store.store(
        "integration_123",
        Credentials(
            client_id =  "Client1",
            client_secret = "Secret",
        )
    )

    credential = store.get("integration_12")
    assert credential ==  None

def test_store_delete_credential(tmp_path):

    key = Fernet.generate_key()
    store = LocalCredentialStore(path=tmp_path / "creds.json", fernet_key=key)

    store.store(
        "integration_123",
        Credentials(
            client_id =  "Client1",
            client_secret = "Secret",
        )
    )

    store.delete("integration_123")
    credential = store.get("integration_123")
    assert credential == None
