from pathlib import Path
import sys ; sys.path.append(str(Path('../../..').resolve()))
from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from utils.dynamic_cat.dynamic_catalog import get_catalogs, get_bugsnag_key, get_env, get_env_token, get_host
from typing_extensions import Optional, Union, Literal
from pyspark.sql.types import StructType
SERVICE_CATALOGS = ['bronze', 'silver', 'gold']


class JobTable():
    """
    Classe factory que implementa algumas facilidades para trabalhar com as tabelas de serviço do Databricks sem usar tantas strings no codigo das tasks.
    """
    def __init__(self, catalog: str, schema: str, tblname: str, description: Optional[str] = None, spark_ddl: Optional[StructType] = None):
        for param, value in {'catalog': catalog, 'schema': schema, 'tblname': tblname}.items():
            if not isinstance(value, str):
                raise TypeError(f"Parameter '{param}' must be a string, got {type(value).__name__}")
        self.schema = schema
        self.tblname = tblname
        self.catalog = self._parse_catalog(catalog)
        self.path = self._parse_path(self.catalog, self.schema, self.tblname)
        self.spark_ddl = spark_ddl

    def _parse_catalog(self, catalog: str):
        if catalog not in SERVICE_CATALOGS:
            raise ValueError(f"Invalid catalog name '{catalog}'. Allowed: {SERVICE_CATALOGS}")
        return get_catalogs().get(catalog, catalog)
    
    def _parse_path(self, catalog: str, schema: str, tblname: str):
        return f"{catalog}.{schema}.{tblname}"

    def get_ddl_from_databricks(self) -> StructType:
        """
        Retorna o schema da tabela no formato StructType do Spark.
        """
        try:
            spark.catalog.tableExists(self.path)
        except NameError as e:
            from databricks.connect import DatabricksSession
            spark = DatabricksSession.builder.getOrCreate()
        if not spark.catalog.tableExists(self.path):
            self.spark_ddl = None
            raise ValueError(f"Tabela '{self.path}' não existe no catálogo.")
        if self.spark_ddl is None:
            self.spark_ddl = spark.table(self.path).schema
        return self.spark_ddl
