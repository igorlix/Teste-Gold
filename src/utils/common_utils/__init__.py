from .environment_utils import whereami_databricks
from .job_table import JobTable
from typing_extensions import Literal
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ServiceCatalogs: 
    BRONZE: str = 'bronze'
    SILVER: str = 'silver'
    GOLD: str = 'gold'
    ALL: list[str] = field(default_factory= lambda: ['bronze', 'silver', 'gold'])

ENGINEERING_CATALOG = 'data_engineering'
__all__ = ["whereami_databricks", "JobTable", "ServiceCatalogs"]
