"""
Configurações da API carregadas de variáveis de ambiente.
"""
import os
from pathlib import Path
from typing import Optional


class Settings:
    """Configurações centralizadas da API"""

    # Versão da API
    VERSION: str = "1.0.0"
    APP_NAME: str = "Busca Avançada API"
    DESCRIPTION: str = "API de busca avançada para catálogo de livros usando busca fuzzy e semântica"

    # Ambiente
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    WHO_IS_RUNNING_THIS: str = os.getenv("WHO_IS_RUNNING_THIS", "ENDPOINT_MLFLOW")

    # Databricks
    DATABRICKS_HOST: Optional[str] = os.getenv("DATABRICKS_HOST")
    DATABRICKS_TOKEN: Optional[str] = os.getenv("DATABRICKS_TOKEN")

    # AWS Bedrock
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-2")
    AWS_BEDROCK_MODEL_ID: str = os.getenv("AWS_BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")

    # LLM Provider
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "bedrock")

    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Health check
    ENABLE_HEALTH_CHECK: bool = os.getenv("ENABLE_HEALTH_CHECK", "true").lower() == "true"

    # CSV Path
    @staticmethod
    def get_csv_path() -> Path:
        """Retorna o caminho do CSV de livros"""
        # Tenta diferentes localizações do CSV
        possible_paths = [
            Path(__file__).parent.parent / "src" / "gold" / "busca" / "books_search.csv",
            Path("/app/src/gold/busca/books_search.csv"),  # Path no Docker
            Path("./src/gold/busca/books_search.csv"),  # Path relativo
        ]

        for path in possible_paths:
            if path.exists():
                return path

        raise FileNotFoundError(
            f"CSV file not found. Tried paths: {[str(p) for p in possible_paths]}"
        )

    @staticmethod
    def validate():
        """Valida se as configurações obrigatórias estão definidas"""
        errors = []

        # Validação específica por provider
        llm_provider = Settings.LLM_PROVIDER.lower()

        if llm_provider == "databricks":
            if not Settings.DATABRICKS_HOST:
                errors.append("DATABRICKS_HOST is required when using databricks provider")
            if not Settings.DATABRICKS_TOKEN:
                errors.append("DATABRICKS_TOKEN is required when using databricks provider")

        if llm_provider not in ["databricks", "bedrock"]:
            errors.append(f"LLM_PROVIDER must be 'databricks' or 'bedrock', got '{llm_provider}'")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

    @staticmethod
    def get_info() -> dict:
        """Retorna informações sobre as configurações (sem dados sensíveis)"""
        return {
            "version": Settings.VERSION,
            "environment": Settings.ENVIRONMENT,
            "llm_provider": Settings.LLM_PROVIDER,
            "aws_region": Settings.AWS_REGION,
            "databricks_configured": bool(Settings.DATABRICKS_HOST and Settings.DATABRICKS_TOKEN),
            "aws_configured": bool(Settings.AWS_REGION),
        }


# Instância global de configurações
settings = Settings()
