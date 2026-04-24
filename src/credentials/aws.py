from base import CredentialStore
from models import Credentials
import boto3
from botocore.exceptions import ClientError
import json

class AwsCredentialStore(CredentialStore):
    def __init__(self, region:str, secret_prefix: str):
        self._prefix = secret_prefix
        self._client = boto3.client('secretsmanager',region_name=region)


    def get(self, integration_id: str) -> Credentials | None:
        if not integration_id or not integration_id.strip():
            raise ValueError("integration_id cannot be empty")
        try:
            response = self._client.get_secret_value(SecretId=f'{self._prefix}{integration_id}')
            return Credentials(**json.loads(response['SecretString']))
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return None
            raise



    def store(self, integration_id: str, credentials: Credentials) -> None:
        self._client.put_secret_value(
            SecretId=f'{self._prefix}{integration_id}',
            SecretString=credentials.model_dump_json(),
        )


    def delete(self, integration_id: str) -> None:
        self._client.delete_secret(
            SecretId=f'{self._prefix}{integration_id}',
            ForceDeleteWithoutRecovery=True,
)