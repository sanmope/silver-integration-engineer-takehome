# demo.py
import os
os.environ["BASE_URL"] = "http://localhost:8000"
import sys

from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cryptography.fernet import Fernet


def ensure_fernet_key() -> bytes:
    env_path = Path(".env")
    env_content = env_path.read_text() if env_path.exists() else ""

    if "FERNET_KEY=" not in env_content or "your-fernet-key-here" in env_content:
        key = Fernet.generate_key().decode()
        with open(env_path, "a") as f:
            f.write(f"\nFERNET_KEY={key}\n")
        print(f"Generated and saved FERNET_KEY to .env")
        os.environ["FERNET_KEY"] = key
        return key.encode()

    # Already in .env — read from config
    from config import config
    print(f"base_url: {config.base_url}")
    return config.fernet_key.encode()


def main():
    fernet_key = ensure_fernet_key()

    # Import after key is set
    from config import config
    from credentials.local import LocalCredentialStore
    from models import Credentials
    from jobs.tasks import sync_vendor_indicators

    # 1. Store credentials
    store = LocalCredentialStore(
        path=config.credentials_path,
        fernet_key=fernet_key,
    )
    store.store(
        "integration_123",
        Credentials(
            client_id="test_client",
            client_secret="test_secret",
        )
    )
    print("✓ Credentials stored for integration_123")

    # 2. Run sync
    print("Running sync against mock server...")
    result = sync_vendor_indicators.apply(args=["integration_123"]).get()

    if result:
        print(f"✓ Sync complete — fetched={result.indicators_fetched}, new={result.indicators_new}, updated={result.indicators_updated}")
    else:
        print("✗ Sync failed — check mock server is running on port 8000")


if __name__ == "__main__":
    main()