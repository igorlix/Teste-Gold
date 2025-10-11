# Busca-avancada-Gold

Sistema de busca avançada para catálogo de livros usando técnicas de busca fuzzy e semântica com Databricks Vector Search.

## Características

- **Busca Fuzzy**: Correspondências aproximadas usando RapidFuzz
- **Busca Semântica**: Busca por significado usando embeddings e Databricks Vector Search
- **RRF (Reciprocal Rank Fusion)**: Combina resultados de diferentes métodos de busca
- **Execução Local**: Suporte para execução local usando credenciais Databricks via .env

## Requisitos

- **Python 3.10 ou 3.11** (Recomendado para Windows - evita problemas de compilação)
- Python 3.8+ (mínimo)
- Acesso ao Databricks (host e token)
- Dependências listadas em `requirements.txt`

## Instalação

> **WINDOWS:** Se você está no Windows com Python 3.13, **recomendamos usar Python 3.10 ou 3.11** para evitar problemas de compilação. Veja o guia: [PYTHON_SETUP.md](PYTHON_SETUP.md)

> **Problemas na instalação?** Consulte o [INSTALL.md](INSTALL.md) para troubleshooting detalhado.

### Instalação Rápida

1. Clone o repositório
2. Instale as dependências:
```bash
# Método 1: Via requirements.txt
pip install -r requirements.txt

# Método 2: Instalação direta (recomendado)
pip install pandas python-dotenv rapidfuzz databricks-vectorsearch databricks-langchain
```

3. Edite o arquivo `.env.example`, renomeie para `.env` e adicione suas credenciais:
```
DATABRICKS_HOST=seu-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef
WHO_IS_RUNNING_THIS=local
```

## Execução Local

Existem duas formas de testar localmente:

### Opção 1: Script de teste dedicado 

```bash
python test_local.py
```

O script executa múltiplos testes:
- Busca por texto livre ("Lei Maria da Penha")
- Busca por campos específicos (título: "Python")

### Opção 2: Executar o main.py diretamente

Navegue até a pasta do módulo e execute:

```bash
cd src/gold/busca
python main.py
```

O arquivo [main.py](src/gold/busca/main.py) agora possui um bloco `if __name__ == "__main__"` que:
- Carrega automaticamente as credenciais do `.env`
- Define `WHO_IS_RUNNING_THIS=local`
- Executa uma busca de exemplo
- Exibe os resultados formatados

## Estrutura do Projeto

```
Busca-avancada-Gold/
├── src/
│   ├── gold/
│   │   └── busca/              # Módulo principal de busca
│   │       ├── main.py         # Função de consolidação
│   │       ├── fuzzy_search.py # Implementação de busca fuzzy
│   │       ├── semantic_search.py  # Implementação de busca semântica
│   │       ├── rrf.py          # Reciprocal Rank Fusion
│   │       └── books_search.csv    # Dataset de livros
│   └── utils/                  # Utilitários compartilhados
│       ├── dynamic_cat/        # Configuração dinâmica de catálogos
│       ├── aws_utils/          # Utilitários AWS
│       └── bugsnag_utils/      # Configuração Bugsnag
├── test_local.py               # Script de teste local
├── .env.example                # Exemplo de configuração
└── requirements.txt            # Dependências Python
```

## Como Funciona

### 1. Busca por Texto Livre
```python
data = {
    'searchQuery': 'Lei Maria da Penha',
    'selectedFields': {},
    'userCatalogs': ['uuid1', 'uuid2']
}
```
Combina busca exata, fuzzy e semântica usando RRF.

### 2. Busca por Campos Específicos
```python
data = {
    'searchQuery': '',
    'selectedFields': {
        'titulo': 'Python',
        'autores': 'Guido',
        'isbn': ''
    },
    'userCatalogs': ['uuid1', 'uuid2']
}
```
Busca fuzzy nos campos especificados.

## Modos de Execução

O código suporta três modos através da variável `WHO_IS_RUNNING_THIS`:

1. **`local`**: Execução local com credenciais do .env
2. **`ENDPOINT_NOTEBOOK`**: Execução em notebook Databricks
3. **`ENDPOINT_MLFLOW`**: Execução em endpoint MLflow Databricks

## Configuração do Databricks

### Obter Token de Acesso

1. Acesse seu workspace Databricks
2. Vá em **User Settings** > **Access Tokens**
3. Clique em **Generate New Token**
4. Copie o token gerado

### Host do Databricks

O host é o domínio do seu workspace (sem `https://`):
- Exemplo: `dbc-a1b2c3d4-e5f6.cloud.databricks.com`
