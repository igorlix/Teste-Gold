import logging
import rich
import sys
from utils.common_utils.environment_utils import detect_environment
from datetime import datetime
_dtstr = lambda: "[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().handlers[0].setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

class Logger:
    """
    Repositório de metodos que direcionam o output de logging com base no ambiente
    """
    try:
        whereami = detect_environment(spark)
    except:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        whereami = detect_environment(spark)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    @classmethod
    def info(cls, message):
        if cls.whereami == "dev":
            rich.print(f"[blue]{_dtstr()} - INFO - {message}[/]")
        else:
            logging.info(f"{message}")

    @classmethod
    def warning(cls, message):
        if cls.whereami == "dev":
            rich.print(f"[orange]{_dtstr()} - WARNING - {message}[/]")
        else:
            logging.warning(f"{message}")

    @classmethod
    def error(cls, message):
        if cls.whereami == "dev":
            rich.print(f"[white on dark red]{_dtstr()} - ERROR - {message}[/]")
        else:
            logging.error(f"{message}")

    @classmethod
    def ok(cls):
        if cls.whereami == "dev":
            rich.print(f"[white on dark green]{_dtstr()} - INFO - [bold]... OK[/][/]\n")
        else:
            logging.info(f"... OK")