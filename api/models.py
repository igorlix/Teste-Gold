"""
Modelos Pydantic para validação de requisições e respostas da API.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class SelectedFields(BaseModel):
    """Campos selecionados para busca específica"""
    titulo: Optional[str] = Field(default="", description="Título do livro")
    autores: Optional[str] = Field(default="", description="Autores do livro")
    assunto: Optional[str] = Field(default="", description="Assunto do livro")
    isbn: Optional[str] = Field(default="", description="ISBN do livro")


class SearchRequest(BaseModel):
    """
    Requisição de busca avançada.

    Exemplos:
        Busca por texto livre:
        {
            "searchQuery": "Lei Maria da Penha",
            "selectedFields": {},
            "userCatalogs": ["uuid1", "uuid2"]
        }

        Busca por campos específicos:
        {
            "searchQuery": "",
            "selectedFields": {"titulo": "Python", "autores": "Guido"},
            "userCatalogs": ["uuid1", "uuid2"]
        }
    """
    searchQuery: str = Field(
        default="",
        description="Texto livre para busca semântica e fuzzy",
        examples=["Lei Maria da Penha", "Python programming"]
    )
    selectedFields: Dict[str, str] = Field(
        default_factory=dict,
        description="Campos específicos para busca (titulo, autores, assunto, isbn)",
        examples=[{"titulo": "Python", "autores": ""}]
    )
    userCatalogs: List[str] = Field(
        ...,
        description="Lista de UUIDs dos catálogos do usuário",
        min_length=1,
        examples=[["538f6227-897a-4a58-8e31-a5fa5b3f9843"]]
    )
    provider: Optional[str] = Field(
        default=None,
        description="Provider LLM: 'databricks' ou 'bedrock'. Se None, usa LLM_PROVIDER do .env",
        examples=["databricks", "bedrock"]
    )

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        if v is not None and v not in ['databricks', 'bedrock']:
            raise ValueError("provider deve ser 'databricks' ou 'bedrock'")
        return v


class BookResult(BaseModel):
    """Resultado de um livro encontrado"""
    uuid: str = Field(..., description="UUID único do livro")
    title: str = Field(..., description="Título do livro")
    authors: str = Field(..., description="Autores do livro")
    score: float = Field(..., description="Score de relevância (0-1 ou >1 para exact matches)")
    method: str = Field(..., description="Método de busca usado (exact, semantic, fuzzy)")


class SearchResponse(BaseModel):
    """Resposta da busca"""
    success: bool = Field(..., description="Se a busca foi bem-sucedida")
    results: List[BookResult] = Field(
        default_factory=list,
        description="Lista de livros encontrados ordenados por score"
    )
    error: Optional[str] = Field(
        default=None,
        description="Mensagem de erro se success=False"
    )
    total_results: int = Field(..., description="Número total de resultados")
    llm_provider: Optional[str] = Field(
        default=None,
        description="Provider LLM usado (databricks ou bedrock)"
    )
    llm_suggestion: Optional[str] = Field(
        default=None,
        description="Sugestão refinada pelo LLM (apenas para busca semântica)"
    )
    llm_used_fallback: Optional[bool] = Field(
        default=False,
        description="Se o LLM falhou e usou fallback para texto original"
    )


class HealthResponse(BaseModel):
    """Resposta do endpoint de health check"""
    status: str = Field(..., description="Status da API (healthy, unhealthy)")
    version: str = Field(..., description="Versão da API")
    environment: str = Field(..., description="Ambiente de execução")
    databricks_connected: bool = Field(..., description="Se está conectado ao Databricks")
    aws_bedrock_available: bool = Field(..., description="Se AWS Bedrock está disponível")
    csv_loaded: bool = Field(..., description="Se o CSV de livros foi carregado")
    total_books: int = Field(..., description="Número total de livros no dataset")
