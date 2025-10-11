import sys, boto3, json, os
from pathlib import Path
sys.path.append(str(Path('../..').resolve()))

runner = str(os.getenv("WHO_IS_RUNNING_THIS"))
if runner == "ENDPOINT_MLFLOW":
    from aws_utils import assume_role
else:
    from utils.aws_utils import assume_role

from botocore.exceptions import ClientError

def get_secret(secret_name, default_region = 'us-east-1'):
    temp_credentials = assume_role(741592248876,"databricks_secrets_manager_read_write").get('Credentials')
    client = boto3.client('secretsmanager', region_name=default_region,
                        aws_access_key_id=temp_credentials['AccessKeyId'],
                        aws_secret_access_key=temp_credentials['SecretAccessKey'],
                        aws_session_token=temp_credentials['SessionToken'])
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
            print("Erro ao acessar o segredo:", e)
    secret_dict = json.loads(get_secret_value_response['SecretString'])
    return secret_dict


def list_secrets(default_region = 'us-east-1'):
    temp_credentials = assume_role(741592248876,"databricks_secrets_manager_read_write").get('Credentials')
    client = boto3.client('secretsmanager', region_name=default_region,
                        aws_access_key_id=temp_credentials['AccessKeyId'],
                        aws_secret_access_key=temp_credentials['SecretAccessKey'],
                        aws_session_token=temp_credentials['SessionToken'])
    try:
        list_secrets_response = client.list_secrets()
    except ClientError as e:
            print("Erro ao listar os segredos:", e)
    for secret in list_secrets_response['SecretList']:
        print(f"Name: {secret['Name']}, ARN: {secret['ARN']}")
    return list_secrets_response['SecretList']



#
