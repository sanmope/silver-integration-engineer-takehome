from abc import ABC, abstractmethod

from models import Credentials


class CredentialStore(ABC):

    @abstractmethod
    def get(self, integration_id: str) -> Credentials | None: ...

    @abstractmethod
    def store(self, integration_id: str, credentials: Credentials) -> None: ...

    @abstractmethod
    def delete(self, integration_id: str) -> None: ...

    


