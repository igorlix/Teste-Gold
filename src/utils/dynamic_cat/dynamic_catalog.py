import os

from dotenv import load_dotenv
from pyspark.sql import SparkSession

from databricks.connect import DatabricksSession


class env_config:
    DATABRICKS_URL_DEV = "dbc-2d42362d-a968.cloud.databricks.com"
    DATABRICKS_URL_UAT = "dbc-f798371e-9252.cloud.databricks.com"
    DATABRICKS_URL_PRD = "dbc-a69fca3f-7d13.cloud.databricks.com"

    ENV_NAME_DEV = "dev"
    ENV_NAME_UAT = "uat"
    ENV_NAME_PRD = "prd"

    BRONZE_CATALOG_NAME_DEV = "bronze_mb_dev"
    BRONZE_CATALOG_NAME_UAT = "bronze_mb_uat"
    BRONZE_CATALOG_NAME_PRD = "bronze_mb_prd"

    SILVER_CATALOG_NAME_DEV = "silver_mb_dev"
    SILVER_CATALOG_NAME_UAT = "silver_mb_uat"
    SILVER_CATALOG_NAME_PRD = "silver_mb_prd"

    GOLD_CATALOG_NAME_DEV = "gold_mb_dev"
    GOLD_CATALOG_NAME_UAT = "gold_mb_uat"
    GOLD_CATALOG_NAME_PRD = "gold_mb_prd"

    DATABRICKS_TOKEN_DEV = "DATABRICKS_TOKEN_DEV"
    DATABRICKS_TOKEN_UAT = "DATABRICKS_TOKEN_UAT"
    DATABRICKS_TOKEN_PRD = "DATABRICKS_TOKEN"
    
    BUGSNAG_API_KEY_DEV = "BUGSNAG_API_KEY_DEV"
    BUGSNAG_API_KEY_UAT = "BUGSNAG_API_KEY_UAT"
    BUGSNAG_API_KEY_PRD = "BUGSNAG_API_KEY"

env_config = env_config()

def _spark():
    try:
        spark.conf.get("spark.databricks.workspaceUrl")
        return spark
    except:
        try:
            # Fallback para Databricks Connect      
            from databricks.connect import DatabricksSession
            spark = DatabricksSession.builder.getOrCreate()
            spark.conf.get("spark.databricks.workspaceUrl")
            return spark
        except:
            # Fallback para SparkSession local
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.getOrCreate()
            return spark

def get_catalogs():
    """
    Retorna os nomes dos catálogos bronze, silver e gold de acordo com o ambiente Databricks detectado.
    """
    spark = _spark()
    workspace_url = spark.conf.get("spark.databricks.workspaceUrl").lower()
    
    if workspace_url == env_config.DATABRICKS_URL_DEV:
        env = env_config.ENV_NAME_DEV
    elif workspace_url == env_config.DATABRICKS_URL_UAT:
        env = env_config.ENV_NAME_UAT
    elif workspace_url == env_config.DATABRICKS_URL_PRD:
        env = env_config.ENV_NAME_PRD

    catalogs = {
        "dev": {
            "bronze": env_config.BRONZE_CATALOG_NAME_DEV,
            "silver": env_config.SILVER_CATALOG_NAME_DEV,
            "gold": env_config.GOLD_CATALOG_NAME_DEV
        },
        "uat": {
            "bronze": env_config.BRONZE_CATALOG_NAME_UAT,
            "silver": env_config.SILVER_CATALOG_NAME_UAT,
            "gold": env_config.GOLD_CATALOG_NAME_UAT
        },
        "prd": {
            "bronze": env_config.BRONZE_CATALOG_NAME_PRD,
            "silver": env_config.SILVER_CATALOG_NAME_PRD,
            "gold": env_config.GOLD_CATALOG_NAME_PRD
        }
    }

    catalogs_dict = {
        "bronze": catalogs[env]["bronze"],
        "silver": catalogs[env]["silver"],
        "gold": catalogs[env]["gold"]
    }
    return catalogs_dict


def get_host():
    """
    Retorna a URL do workspace Databricks atual.
    Se rodando localmente, retorna do .env.
    """
    # Se rodando localmente, pega do .env
    if os.getenv("WHO_IS_RUNNING_THIS") == "local" or not os.getenv("DATABRICKS_HOST"):
        load_dotenv()
        databricks_host = os.getenv("DATABRICKS_HOST", "")
        # Remove o https:// se existir
        return databricks_host.replace("https://", "").replace("http://", "")

    # Se rodando no Databricks, pega do Spark
    spark = _spark()
    workspace_url = spark.conf.get("spark.databricks.workspaceUrl").lower()
    return workspace_url

def get_env():
    """
    Retorna o nome do ambiente ('dev', 'uat', 'prd') com base na URL do workspace Databricks.
    Lança exceção se o ambiente não for identificado.
    """
    spark = _spark()
    workspace_url = spark.conf.get("spark.databricks.workspaceUrl").lower()
    
    if workspace_url == env_config.DATABRICKS_URL_DEV:
        env = env_config.ENV_NAME_DEV
    elif workspace_url == env_config.DATABRICKS_URL_UAT:
        env = env_config.ENV_NAME_UAT
    elif workspace_url == env_config.DATABRICKS_URL_PRD:
        env = env_config.ENV_NAME_PRD
    else:
        raise ValueError("Ambiente não identificado!")

    return env


def get_env_token():
    """
    Retorna o nome da variável de token do ambiente Databricks atual.
    Lança exceção se o ambiente não for identificado.
    """
    spark = _spark()
    workspace_url = spark.conf.get("spark.databricks.workspaceUrl").lower()
    
    if workspace_url == env_config.DATABRICKS_URL_DEV:
        token = env_config.DATABRICKS_TOKEN_DEV
    elif workspace_url == env_config.DATABRICKS_URL_UAT:
        token = env_config.DATABRICKS_TOKEN_UAT
    elif workspace_url == env_config.DATABRICKS_URL_PRD:
        token = env_config.DATABRICKS_TOKEN_PRD
    else:
        raise ValueError("Ambiente não identificado!")

    return token


def get_bugsnag_key():
    """
    Retorna o nome da variável de chave da API Bugsnag do ambiente Databricks atual.
    Lança exceção se o ambiente não for identificado.
    """
    spark = _spark()
    workspace_url = spark.conf.get("spark.databricks.workspaceUrl").lower()
    
    if workspace_url == env_config.DATABRICKS_URL_DEV:
        key = env_config.BUGSNAG_API_KEY_DEV
    elif workspace_url == env_config.DATABRICKS_URL_UAT:
        key = env_config.BUGSNAG_API_KEY_UAT
    elif workspace_url == env_config.DATABRICKS_URL_PRD:
        key = env_config.BUGSNAG_API_KEY_PRD
    else:
        raise ValueError("Ambiente não identificado!")

    return key


def get_env_variable(var_base_name):
    """
    Retorna o valor da variável de ambiente correta com base no ambiente Databricks atual.
    Exemplo: Se var_base_name='API_KEY_BUGSNAG' e ambiente='dev', retorna o valor de 'API_KEY_BUGSNAG_DEV' do .env.
    Lança exceção se o ambiente não for identificado.
    """
    load_dotenv()  # Carrega as variáveis do .env
    spark = _spark()
    workspace_url = spark.conf.get("spark.databricks.workspaceUrl").lower()

    if workspace_url == env_config.DATABRICKS_URL_DEV:
        env = env_config.ENV_NAME_DEV
    elif workspace_url == env_config.DATABRICKS_URL_UAT:
        env = env_config.ENV_NAME_UAT
    elif workspace_url == env_config.DATABRICKS_URL_PRD:
        env = env_config.ENV_NAME_PRD
    else:
        raise ValueError("Ambiente não identificado!")

    env_var_name = f"{var_base_name}_{env.upper()}"  # Ex: "API_KEY_BUGSNAG_DEV"
    return os.getenv(env_var_name)  # Retorna o valor da variável do .env
