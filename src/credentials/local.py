from pathlib import Path
import json

from cryptography.fernet import Fernet

from models import Credentials

from credentials.base import CredentialStore
from pydantic import BaseModel

class CredentialFile(BaseModel):
    integrations: dict[str, str]  # integration_id → encrypted bytes (base64)

def load_credential_file(path: Path) -> CredentialFile:
    if path.exists():
        return CredentialFile(
            integrations=json.loads(path.read_bytes().decode("utf-8"))
        )
    else:
        return CredentialFile(integrations={})

def atomic_write_integrations_file(path: Path, integrations: dict) -> None:
    #Atomic write - avoids corruption if process dies in the middle 
    tmp = path.with_suffix('.tmp')
    tmp.write_bytes(json.dumps(integrations, default=str).encode("utf-8"))
    tmp.replace(path)


    

class LocalCredentialStore(CredentialStore):
    def __init__(self, path: str, fernet_key: bytes):
        self._path = Path(path)
        self._fernet = Fernet(fernet_key)
        

    def get(self, integration_id: str) -> Credentials | None:

        #Read from file
        c_file = load_credential_file(self._path)
        if c_file.integrations == {}:
            return None
        if integration_id not in c_file.integrations:
            return None

        #Read string in base64
        encrypted = c_file.integrations[integration_id].encode("utf-8")

        #Decrypt
        data = self._fernet.decrypt(encrypted)

        #Deserialyze
        return Credentials.model_validate_json(data)

        

    def store(self, integration_id: str, credentials: Credentials) -> None:
        
        
        c_file = load_credential_file(self._path)
   
        
        #Serialize  Json -> bytes
        data = credentials.model_dump_json().encode() 

        #Encrypt
        encrypted = self._fernet.encrypt(data)

        #Add encrypted Credential to dict
        c_file.integrations[integration_id] = encrypted.decode("utf-8")


        #Save into .env
        atomic_write_integrations_file(self._path, c_file.integrations)




    def delete(self, integration_id: str) -> None:
        c_file = load_credential_file(self._path)
        if c_file.integrations == {}:
            return None
        
        if integration_id in c_file.integrations:
            del c_file.integrations[integration_id]
            #Save into .env
            atomic_write_integrations_file(self._path, c_file.integrations)
        

