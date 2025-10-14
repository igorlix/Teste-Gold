"""
FastAPI application for advanced book search.
Provides REST API endpoints for fuzzy and semantic search.
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
import logging

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import uvicorn

from api.models import SearchRequest, SearchResponse, HealthResponse, BookResult
from api.config import settings
from gold.busca.main import consolidation_function

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variável global para armazenar o DataFrame
books_df: pd.DataFrame | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Carrega o CSV na inicialização e limpa recursos no shutdown.
    """
    global books_df

    logger.info("="*80)
    logger.info("Starting Busca Avançada API")
    logger.info("="*80)

    # Valida configurações
    try:
        settings.validate()
        logger.info("✓ Configuration validated")
        logger.info(f"  Environment: {settings.ENVIRONMENT}")
        logger.info(f"  LLM Provider: {settings.LLM_PROVIDER}")
        logger.info(f"  AWS Region: {settings.AWS_REGION}")
    except ValueError as e:
        logger.error(f"✗ Configuration error: {e}")
        raise

    # Carrega o CSV
    try:
        csv_path = settings.get_csv_path()
        books_df = pd.read_csv(csv_path, encoding="utf-8")
        logger.info(f"✓ CSV loaded: {len(books_df)} books from {csv_path}")
    except FileNotFoundError as e:
        logger.error(f"✗ CSV not found: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Error loading CSV: {e}")
        raise

    logger.info("="*80)
    logger.info(f"API ready on environment: {settings.ENVIRONMENT}")
    logger.info("="*80)

    yield

    # Cleanup
    logger.info("Shutting down Busca Avançada API")
    books_df = None


# Inicializa FastAPI com lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz com informações básicas da API"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "search": "/api/v1/search"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint para AWS ECS/ALB.
    Retorna status da API e dependências.
    """
    global books_df

    # Testa conexão Databricks (se configurado)
    databricks_ok = False
    if settings.DATABRICKS_HOST and settings.DATABRICKS_TOKEN:
        try:
            # Verifica se as variáveis estão configuradas
            databricks_ok = True
        except Exception as e:
            logger.warning(f"Databricks health check failed: {e}")

    # Testa AWS Bedrock (sempre disponível com IAM role)
    aws_bedrock_ok = True
    try:
        import boto3
        client = boto3.client('bedrock-runtime', region_name=settings.AWS_REGION)
        aws_bedrock_ok = True
    except Exception as e:
        logger.warning(f"AWS Bedrock health check failed: {e}")
        aws_bedrock_ok = False

    # Determina status geral
    csv_ok = books_df is not None and not books_df.empty
    is_healthy = csv_ok and (databricks_ok or aws_bedrock_ok)

    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        databricks_connected=databricks_ok,
        aws_bedrock_available=aws_bedrock_ok,
        csv_loaded=csv_ok,
        total_books=len(books_df) if csv_ok else 0
    )


@app.post("/api/v1/search", response_model=SearchResponse, tags=["Search"])
async def search_books(request: SearchRequest):
    """
    Busca avançada de livros usando busca fuzzy e semântica.

    - **searchQuery**: Texto livre para busca semântica (ex: "Lei Maria da Penha")
    - **selectedFields**: Campos específicos para busca (ex: {"titulo": "Python"})
    - **userCatalogs**: Lista de UUIDs dos catálogos do usuário (obrigatório)
    - **provider**: Provider LLM opcional ("databricks" ou "bedrock")

    Retorna lista de livros ordenados por relevância com scores e métodos de busca.
    """
    global books_df

    if books_df is None or books_df.empty:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Book database not loaded. Service temporarily unavailable."
        )

    # Prepara dados para consolidation_function
    data = {
        "searchQuery": request.searchQuery,
        "selectedFields": request.selectedFields,
        "userCatalogs": request.userCatalogs
    }

    # Define provider LLM se especificado
    original_provider = None
    if request.provider:
        original_provider = os.getenv("LLM_PROVIDER")
        os.environ["LLM_PROVIDER"] = request.provider
        logger.info(f"Using LLM provider: {request.provider}")

    try:
        # Executa a busca
        result = consolidation_function(data, books_df, local=False)

        # Converte resultados para BookResult models
        book_results = [
            BookResult(
                uuid=book.get("uuid"),
                title=book.get("title"),
                authors=book.get("authors"),
                score=book.get("score"),
                method=book.get("method")
            )
            for book in result.get("results", [])
        ]

        # Prepara resposta
        response = SearchResponse(
            success=result.get("success", False),
            results=book_results,
            error=result.get("error"),
            total_results=len(book_results),
            llm_provider=result.get("llm_provider"),
            llm_suggestion=result.get("llm_suggestion"),
            llm_used_fallback=result.get("llm_used_fallback", False)
        )

        # Log da busca
        if response.success:
            logger.info(
                f"Search completed: query='{request.searchQuery}', "
                f"results={response.total_results}, "
                f"provider={response.llm_provider}"
            )
        else:
            logger.warning(
                f"Search failed: query='{request.searchQuery}', "
                f"error={response.error}"
            )

        return response

    except Exception as e:
        logger.error(f"Error during search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during search: {str(e)}"
        )

    finally:
        # Restaura provider original
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider


@app.get("/api/v1/config", tags=["Config"])
async def get_config():
    """
    Retorna configurações da API (sem dados sensíveis).
    """
    return settings.get_info()


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handler para ValueError"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    """Handler para FileNotFoundError"""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": f"Required file not found: {str(exc)}"}
    )


# Entry point para execução direta
if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level=settings.LOG_LEVEL.lower()
    )
