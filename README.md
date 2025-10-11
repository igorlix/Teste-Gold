# Busca Avançada Gold

Sistema de busca avançada para catálogo de livros usando busca fuzzy e semântica com Databricks Vector Search.

## 🚀 Quick Start

### 1. Clonar e Instalar

```bash
# Clone o repositório
git clone <repo-url>
cd Busca-avancada-Gold

# Crie ambiente virtual com Python 3.10 ou 3.11 (recomendado para Windows)
py -3.10 -m venv venv

# Ative o ambiente virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt
```

### 2. Configurar Credenciais

```bash
# Copie o template
cp .env.config .env

# Edite com suas credenciais Databricks
notepad .env  # Windows
nano .env     # Linux/Mac
```

Configure no `.env`:
```ini
DATABRICKS_HOST=seu-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef
WHO_IS_RUNNING_THIS=local
```

### 3. Testar

```bash
# Certifique-se de estar no venv (deve aparecer (venv) no prompt)
python test_local.py
```

## ✨ Características

- **Busca Fuzzy**: Correspondências aproximadas usando RapidFuzz
- **Busca Semântica**: Busca por significado usando Databricks Vector Search
- **RRF**: Combina resultados de diferentes métodos
- **Execução Local**: Roda localmente conectando ao Databricks

## 📋 Requisitos

- Python 3.10 ou 3.11 (recomendado Windows)
- Python 3.8+ (mínimo)
- Credenciais Databricks (host + token)

## 🔧 Configuração do Vector Search

Se precisar criar seu próprio endpoint:

```bash
python setup_vector_search.py
```

Depois atualize [config_semantic_search.py](src/gold/busca/config_semantic_search.py):
```python
vector_search_config = {
    "endpoint_name": "my_books_endpoint",
    "index_table": "gold_mb_dev.busca_avancada.my_books_search_index",
    "table": "bronze_mb_dev.busca_avancada.ebooks_search"
}
```

## 📖 Documentação

- **[MODIFICACOES_LOCAL.md](MODIFICACOES_LOCAL.md)** - Guia completo das modificações para execução local
- **[PYTHON_SETUP.md](PYTHON_SETUP.md)** - Setup detalhado Python 3.10/3.11 no Windows
- **[INSTALL.md](INSTALL.md)** - Troubleshooting de instalação

## 🎯 Como Usar

### Busca por Texto Livre

```python
from gold.busca.main import consolidation_function
import pandas as pd

data = {
    'searchQuery': 'Python',
    'selectedFields': {},
    'userCatalogs': ['uuid1', 'uuid2']
}

file_csv = pd.read_csv("books_search.csv")
result = consolidation_function(data, file_csv, local=True)
```

### Busca por Campos

```python
data = {
    'searchQuery': '',
    'selectedFields': {
        'titulo': 'Python',
        'autores': '',
        'isbn': ''
    },
    'userCatalogs': ['uuid1', 'uuid2']
}
```

## 🔑 Obter Token Databricks

1. Acesse seu workspace: `https://seu-workspace.cloud.databricks.com`
2. User Settings → Access Tokens
3. Generate New Token
4. Copie o token para o `.env`

## 🐛 Troubleshooting

**Erro de permissão no Vector Search?**
- Verifique se tem acesso ao endpoint no Catalog Explorer
- Ou crie seu próprio: `python setup_vector_search.py`

**Erro de compilação no Windows?**
- Use Python 3.10 ou 3.11: veja [PYTHON_SETUP.md](PYTHON_SETUP.md)

**Módulos não encontrados?**
- Ative o venv: `venv\Scripts\activate`
- Reinstale: `pip install -r requirements.txt`

## 📁 Estrutura

```
Busca-avancada-Gold/
├── src/gold/busca/         # Módulo principal
│   ├── main.py             # Função consolidation
│   ├── fuzzy_search.py     # Busca fuzzy
│   ├── semantic_search.py  # Busca semântica
│   └── rrf.py              # RRF
├── test_local.py           # Script de teste
├── setup_vector_search.py  # Setup do Vector Search
└── .env                    # Suas credenciais (não versionar!)
```

## 🔄 Modos de Execução

- `local` - Execução local (via .env)
- `ENDPOINT_NOTEBOOK` - Notebook Databricks
- `ENDPOINT_MLFLOW` - MLflow Endpoint

---

**Precisa de mais detalhes?** Veja [MODIFICACOES_LOCAL.md](MODIFICACOES_LOCAL.md)
