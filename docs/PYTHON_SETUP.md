# Setup com Python 3.10/3.11 (Recomendado para Windows)

## Por que Python 3.10 ou 3.11?

Python 3.13 é muito novo (lançado em 2024) e muitas bibliotecas científicas como scipy ainda não têm **wheels pré-compilados** para ele no Windows. Isso força a compilação durante a instalação, que é lenta e pode dar erro.

Python 3.10 e 3.11 têm todas as dependências pré-compiladas e a instalação é **muito mais rápida**.

## Passo a Passo

### 1. Baixar Python 3.10 ou 3.11

Acesse: https://www.python.org/downloads/

- **Python 3.10.11** (Estável, recomendado): https://www.python.org/downloads/release/python-31011/
- **Python 3.11.9** (Mais recente estável): https://www.python.org/downloads/release/python-3119/

Baixe o instalador **Windows installer (64-bit)**

**IMPORTANTE:** Durante a instalação, marque a opção **"Add Python 3.10 to PATH"**

### 2. Verificar instalação

Abra um **novo** terminal e verifique:

```bash
# Verificar Python 3.10
py -3.10 --version

# Ou Python 3.11
py -3.11 --version
```

Deve mostrar algo como: `Python 3.10.11` ou `Python 3.11.9`

### 3. Criar ambiente virtual com Python 3.10

No diretório do projeto:

```bash
# Navegar para o projeto
cd D:\Documentos\GitHub\Busca-avancada-Gold

# Criar ambiente virtual com Python 3.10
py -3.10 -m venv venv

# Ou com Python 3.11
py -3.11 -m venv venv
```

### 4. Ativar o ambiente virtual

```bash
# Windows Command Prompt
venv\Scripts\activate

# Windows PowerShell
venv\Scripts\Activate.ps1

# Git Bash
source venv/Scripts/activate
```

Você verá `(venv)` no início da linha do terminal.

### 5. Atualizar pip

```bash
python -m pip install --upgrade pip
```

### 6. Instalar dependências

```bash
# Instalação completa (será MUITO mais rápido agora!)
pip install -r requirements.txt

# Ou instalar diretamente:
pip install pandas python-dotenv rapidfuzz databricks-vectorsearch databricks-langchain
```

Deve completar em 2-5 minutos (ao invés de 30+ minutos).

### 7. Configurar credenciais

```bash
# Copiar template
cp .env.config .env

# Editar com suas credenciais (use notepad ou seu editor favorito)
notepad .env
```

Configure:
```ini
DATABRICKS_HOST=seu-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef
WHO_IS_RUNNING_THIS=local
```

### 8. Testar!

```bash
python test_local.py
```

## Verificação Rápida

Para confirmar que está usando o Python correto do ambiente virtual:

```bash
python --version
# Deve mostrar Python 3.10.x ou 3.11.x

python -c "import sys; print(sys.executable)"
# Deve mostrar o caminho do venv: D:\Documentos\...\venv\Scripts\python.exe
```



## Alternativa: Instalar apenas Python 3.10 como padrão

Se preferir, você pode desinstalar Python 3.13 e instalar apenas Python 3.10 como versão padrão. Assim não precisa especificar `-3.10` toda vez.

### PowerShell bloqueia execução de scripts

Se aparecer erro ao ativar:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

## Resumo dos Comandos

```bash
# 1. Criar venv
py -3.10 -m venv venv

# 2. Ativar
venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar .env
cp .env.config .env
notepad .env

# 5. Testar
python test_local.py
```

Pronto! Com Python 3.10 ou 3.11, a instalação será rápida e sem erros de compilação.
