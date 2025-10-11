import sys
from pathlib import Path
sys.path.append(str(Path('../..').resolve()))
import databricks.sdk.dbutils as dbutils
import boto3
from botocore.exceptions import ClientError


def assume_role(target_account_id: int, role_name: str):
    ak = dbutils.RemoteDbUtils().secrets.get(scope="aws", key="aws_access_key_id")
    sk = dbutils.RemoteDbUtils().secrets.get(scope="aws", key="aws_secret_access_key")
    rn = dbutils.RemoteDbUtils().secrets.get(scope="aws", key="region_name")
    try:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=ak,
            aws_secret_access_key=sk,
            region_name=rn
        )
    except ClientError as e:
        print(f"Error creating STS client: {e}")
        raise
    assume_role_kwargs = {
        "RoleArn": f"arn:aws:iam::{target_account_id}:role/{role_name}",
        "RoleSessionName": f"cross-account-session-{target_account_id}"
    }
    return sts_client.assume_role(**assume_role_kwargs)

#