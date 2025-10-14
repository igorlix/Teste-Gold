# Busca Avançada API

API REST para busca avançada de livros usando busca fuzzy e semântica com FastAPI.

---

## Visão Geral

Esta API fornece endpoints para realizar buscas avançadas em um catálogo de livros usando:
- **Busca Fuzzy**: Correspondências aproximadas usando RapidFuzz
- **Busca Semântica**: Busca por significado usando Databricks Vector Search
- **RRF (Reciprocal Rank Fusion)**: Combina resultados de diferentes métodos
- **Multi-Provider LLM**: Suporte para Databricks ou AWS Bedrock (Amazon Nova)

---

## Arquitetura

```
┌──────────────────┐
│   FastAPI App    │
│   (Uvicorn)      │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
┌───▼────┐ ┌─▼──────────┐
│ Fuzzy  │ │  Semantic  │
│ Search │ │  Search    │
└───┬────┘ └─┬──────────┘
    │        │
    └────┬───┘
         │
    ┌────▼────┐
    │   RRF   │
    │ Fusion  │
    └────┬────┘
         │
    ┌────▼─────────┐
    │  AWS Bedrock │
    │ Amazon Nova  │
    └──────────────┘
```

---

## Instalação e Execução Local

### Pré-requisitos

```bash
# Python 3.11+
python --version

# AWS CLI configurado (se usar Bedrock)
aws configure
```

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt
```

### Execução Direta

```bash
# Definir variáveis de ambiente
export LLM_PROVIDER=bedrock
export AWS_REGION=us-east-2
export WHO_IS_RUNNING_THIS=ENDPOINT_MLFLOW

# Executar API
python -m api.main

# ou
uvicorn api.main:app --reload --host 0.0.0.0 --port 9001
```

### Execução com Docker

```bash
# Build da imagem
docker build -t busca-avancada-api .

# Run do container
docker run -p 9001:9001 \
  -e LLM_PROVIDER=bedrock \
  -e AWS_REGION=us-east-2 \
  -v ~/.aws:/home/appuser/.aws:ro \
  busca-avancada-api
```

### Execução com Docker Compose

```bash
# Start
docker-compose up -d

# Ver logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Endpoints

### GET `/`
Informações básicas da API

**Response:**
```json
{
  "app": "Busca Avançada API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "search": "/api/v1/search"
}
```

### GET `/health`
Health check para AWS ECS/ALB

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "databricks_connected": false,
  "aws_bedrock_available": true,
  "csv_loaded": true,
  "total_books": 93849
}
```

### POST `/api/v1/search`
Busca avançada de livros

**Request Body:**
```json
{
  "searchQuery": "Lei Maria da Penha",
  "selectedFields": {},
  "userCatalogs": [
    "538f6227-897a-4a58-8e31-a5fa5b3f9843"
  ],
  "provider": "bedrock"
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "uuid": "b4fb5070-a89e-4259-b4e4-c18407e9f23b",
      "title": "A vida, a saúde e a segurança das mulheres",
      "authors": "Fabíola Sucasas",
      "score": 0.98,
      "method": "semantic"
    }
  ],
  "error": null,
  "total_results": 6,
  "llm_provider": "bedrock",
  "llm_suggestion": "Legislação brasileira sobre proteção...",
  "llm_used_fallback": false
}
```

### GET `/api/v1/config`
Configurações da API (sem dados sensíveis)

**Response:**
```json
{
  "version": "1.0.0",
  "environment": "production",
  "llm_provider": "bedrock",
  "aws_region": "us-east-2",
  "databricks_configured": false,
  "aws_configured": true
}
```

### GET `/docs`
Documentação interativa Swagger UI

### GET `/redoc`
Documentação ReDoc

---

## Variáveis de Ambiente

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `LLM_PROVIDER` | Provider LLM (databricks/bedrock) | `bedrock` | Sim |
| `AWS_REGION` | Região AWS | `us-east-2` | Sim (se bedrock) |
| `AWS_BEDROCK_MODEL_ID` | Model ID Bedrock | `us.amazon.nova-pro-v1:0` | Não |
| `DATABRICKS_HOST` | Host Databricks | - | Sim (se databricks) |
| `DATABRICKS_TOKEN` | Token Databricks | - | Sim (se databricks) |
| `ENVIRONMENT` | Ambiente (production/development) | `production` | Não |
| `WHO_IS_RUNNING_THIS` | Modo de execução | `ENDPOINT_MLFLOW` | Não |
| `LOG_LEVEL` | Nível de log (INFO/DEBUG/WARNING) | `INFO` | Não |
| `CORS_ORIGINS` | Origens CORS (separadas por vírgula) | `*` | Não |

---

## Exemplos de Uso

### Python

```python
import requests

url = "http://localhost:9001/api/v1/search"

payload = {
    "searchQuery": "Lei Maria da Penha",
    "selectedFields": {},
    "userCatalogs": ["538f6227-897a-4a58-8e31-a5fa5b3f9843"],
    "provider": "bedrock"
}

response = requests.post(url, json=payload)
print(response.json())
```

### cURL

```bash
curl -X POST "http://localhost:9001/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "searchQuery": "Lei Maria da Penha",
    "selectedFields": {},
    "userCatalogs": ["538f6227-897a-4a58-8e31-a5fa5b3f9843"]
  }'
```

### JavaScript (Fetch)

```javascript
const response = await fetch('http://localhost:9001/api/v1/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    searchQuery: 'Lei Maria da Penha',
    selectedFields: {},
    userCatalogs: ['538f6227-897a-4a58-8e31-a5fa5b3f9843']
  })
});

const data = await response.json();
console.log(data);
```

---

## Estrutura do Projeto

```
api/
├── __init__.py          # Package marker
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── config.py            # Configuration settings
└── README.md            # Este arquivo
```

---

## Deploy

### Docker Build

```bash
# Build
docker build -t busca-avancada-api:v1.0.0 .

# Tag para ECR
docker tag busca-avancada-api:v1.0.0 ${ECR_URI}:v1.0.0

# Push para ECR
docker push ${ECR_URI}:v1.0.0
```


