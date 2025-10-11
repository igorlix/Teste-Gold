# environment_utils
#

from unittest import case
from typing_extensions import Literal, Union
from pyspark.sql import SparkSession
from utils import dynamic_cat
from databricks.sdk import WorkspaceClient

def detect_environment(spark: Union[SparkSession, None] = None) -> Literal["dev", "prd", "unknown", "error"]:
    """
    Detecta o ambiente atual do cluster Databricks com base no nome do cluster.
    Args:
        spark: Sessão Spark ativa.
    Retorna:
        Literal["dev", "prd", "unknown", "error"]: 
            - "dev" se o nome do cluster indicar ambiente de desenvolvimento.
            - "prd" se o nome do cluster indicar ambiente de produção.
            - "unknown (<nome_do_cluster>)" se não for possível identificar o ambiente.
            - "error detecting environment (<mensagem_de_erro>)" em caso de exceção.
    Exemplo:
        ambiente = detect_environment(spark)
    """
    if spark is None:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()

    try:
        cluster_name = spark.conf.get("spark.databricks.clusterUsageTags.clusterName", "Unknown")
        cluster_name_lower = cluster_name.lower()
        if "dev" in cluster_name_lower:
            return "dev"
        elif "prd" in cluster_name_lower or "prod" in cluster_name_lower:
            return "prd"
        else:
            return f"unknown ({cluster_name})"
    except Exception as e:
        return f"error detecting environment ({str(e)})"



# whereami_databricks
def whereami_databricks():
    """
    Retorna informações sobre o ambiente Databricks atual.
    - 'env': nome do ambiente (ex: dev, prd)
    - 'env_location': localização do ambiente (cloud ou local)
    - 'host': host do cluster
    - 'service_catalogs': lista de catálogos de serviço
    - 'engineering_catalog': catálogo de engenharia de dados
    Exemplo de uso:
        from utils.common_utils.environment_utils import whereami_databricks
        print(whereami_databricks['env'])
    """
    def get_env_location():
        _ls = WorkspaceClient().dbutils.fs.ls('/')
        if _ls[0].path.startswith('dbfs:/'):
            return 'cloud'
        else:
            return 'local'

    return {
        'env': dynamic_cat.get_env(),
        'env_location': get_env_location(),
        'host': dynamic_cat.get_host(),
        'service_catalogs': dynamic_cat.get_catalogs(),
        'engineering_catalog': 'data_engineering'
    }

#
