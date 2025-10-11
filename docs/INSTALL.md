# Guia de Instalação - Busca Avançada Gold

## Pré-requisitos

- Python 3.8 ou superior
- pip atualizado
- Credenciais Databricks (host e token)

## Instalação Passo a Passo

### 1. Instalar Dependências

**IMPORTANTE:** No Windows, as dependências do Databricks podem requerer Visual Studio Build Tools. Siga a ordem abaixo:

```bash
# Atualiza pip
python -m pip install --upgrade pip

# Instala dependências básicas primeiro
pip install pandas python-dotenv rapidfuzz

# Instala dependências Databricks (pode demorar)
pip install databricks-vectorsearch databricks-langchain
```

**Alternativa para evitar erro de compilação:**

Se você encontrar erros de compilação (scipy, numpy, etc.), instale versões pré-compiladas:

```bash
# Windows: Use wheels pré-compilados
pip install pandas python-dotenv rapidfuzz --only-binary :all:

# Databricks
pip install databricks-vectorsearch databricks-langchain
```

### 2. Configurar Credenciais

```bash
# Copia o template de configuração
cp .env.config .env

# Edite o arquivo .env com suas credenciais
notepad .env  # ou use seu editor favorito
```

Adicione suas credenciais no arquivo `.env`:

```ini
DATABRICKS_HOST=seu-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef
WHO_IS_RUNNING_THIS=local
```

### 3. Verificar Instalação

Execute o teste para verificar se tudo está funcionando:

```bash
python test_local.py
```

## Troubleshooting

### Erro: "No module named 'rapidfuzz'"

```bash
pip install rapidfuzz
```

### Erro: "No module named 'databricks'"

```bash
pip install databricks-vectorsearch databricks-langchain
```

### Erro: scipy compilation error (Windows)

Este é um problema comum no Windows. Soluções:

**Opção 1: Usar versão Python compatível**
- Use Python 3.10 ou 3.11 (evite 3.13 que é muito novo)

**Opção 2: Instalar Build Tools**
- Baixe e instale [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)
- Selecione "Desktop development with C++"

**Opção 3: Usar ambiente conda**
```bash
conda create -n busca-avancada python=3.10
conda activate busca-avancada
conda install pandas numpy scipy
pip install -r requirements.txt
```

### Erro: "DATABRICKS_HOST and DATABRICKS_TOKEN must be set"

Verifique se:
1. O arquivo `.env` existe na raiz do projeto
2. As variáveis estão definidas corretamente
3. Não há espaços extras nas linhas

### Erro: "No module named 'fuzzy_search'"

Certifique-se de estar executando o script da raiz do projeto:

```bash
# Correto (da raiz)
python test_local.py

# Incorreto
cd src/gold/busca
python ../../test_local.py  # Não funciona
```

## Instalação Completa 

Para evitar problemas, use este comando único:

```bash
pip install pandas>=2.0.0 python-dotenv>=1.0.0 rapidfuzz>=3.0.0 databricks-vectorsearch>=0.22 databricks-langchain>=0.1.0
```

## Verificação Rápida

Para testar se as dependências foram instaladas:

```python
python -c "import pandas, rapidfuzz, dotenv, databricks.vector_search; print('Todas as dependências instaladas!')"
```

Se este comando executar sem erros, você está pronto para usar o sistema!
