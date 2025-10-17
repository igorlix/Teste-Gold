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
        examples=["Data science"]
    )
    selectedFields: Dict[str, str] = Field(
        default_factory=dict,
        description="Campos específicos para busca (titulo, autores, assunto, isbn)",
        examples=[{"titulo": "", "autores": "", "assunto": "", "isbn": ""}]
    )
    userCatalogs: List[str] = Field(
        ...,
        description="Lista de UUIDs dos catálogos do usuário",
        min_length=1,
        examples=[[
          "538f6227-897a-4a58-8e31-a5fa5b3f9843",
          "081c27c7-d1dc-425e-ba9a-f838df4187ee",
          "68b15a1f-615f-4751-8239-e929f11fa0a8",
          "487eb979-ed08-4ed0-ab3a-9bad0d40420d",
          "9e29e343-8f08-4da6-b61b-ba449c35d766",
          "4a85e11c-3b6d-4760-8829-d9b49d59a4e9",
          "ffa7d139-73bd-4180-b1c5-6844eda14048",
          "fb8905ba-6ce4-4716-9637-d209aeda365a",
          "ea937fd9-454a-4369-bac4-a94db7cbff9d",
          "4bc4dc85-dac6-4556-9008-949e691b0957",
          "f5b33ddb-aab3-44e6-99e2-eaf1d19951ad",
          "1acfd238-a4b4-4150-ba27-b11862c9b539",
          "8f6ec6c1-dd31-4bd1-8d71-616510c6f3fe",
          "7f5a012b-1eab-4e10-b359-c0a8153c0554",
          "8d815eb9-50ef-48f3-ba3d-319a0f420d29",
          "e375d6f8-bf23-4303-8d0e-bd29203d1ef9",
          "69729166-75f1-4993-9c02-fe9b860182e5",
          "c3126820-7665-4ac9-a93b-fb3d8ed3eed0",
          "d0e1e7b7-ba2e-4385-b296-d6f3ec00ab7c",
          "f13ea59c-604d-4903-8b78-8f442f9229de",
          "a9fe6285-3cfc-4521-941a-e5da11b8291a",
          "9d8369e5-0877-465d-ba05-d3efb2a48a67"
        ]]
    )
    provider: Optional[str] = Field(
        default=None,
        description="Provider LLM: 'databricks' ou 'bedrock'. Se None, usa LLM_PROVIDER do .env",
        examples=["databricks"]
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
