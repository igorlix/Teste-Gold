import os
import sys
import time
from typing import Any, Dict, List
import boto3

# from pathlib import Path
# sys.path.append(str((Path.cwd() / Path('../' * 3)).resolve()))

import pandas as pd
from databricks.vector_search.client import VectorSearchClient
from databricks_langchain import ChatDatabricks
from dotenv import load_dotenv

# Carrega variáveis de ambiente para execução local
load_dotenv()

# Importa bugsnag apenas se disponível
try:
    import bugsnag
except ImportError:
    # Mock do bugsnag para ambiente local
    class MockBugsnag:
        @staticmethod
        def notify(exception):
            pass  # Ignora notificações em ambiente local
    bugsnag = MockBugsnag()

runner = str(os.getenv("WHO_IS_RUNNING_THIS"))
if runner=="ENDPOINT_NOTEBOOK":
    from utils.dynamic_cat import dynamic_catalog, env_config
    from utils.aws_utils import secrets
    from model.config_semantic_search import (
        chat_model_config,
        required_columns,
        search_config,
        suggestion_prompt_template,
        vector_search_config,
    )
elif runner=="ENDPOINT_MLFLOW":
    from utils.dynamic_cat import env_config
    from utils.aws_utils import secrets
    from gold.busca.config_semantic_search import (
        chat_model_config,
        bedrock_model_config,
        required_columns,
        search_config,
        suggestion_prompt_template,
        vector_search_config,
    )
    from gold.busca.bedrock_chat import BedrockChat
else: # teste local
    from utils.dynamic_cat import dynamic_catalog, env_config

    # Tenta importar AWS utils (opcional - só usado em prod)
    try:
        from utils.aws_utils import secrets
    except (ImportError, ModuleNotFoundError):
        # Mock para ambiente local sem AWS
        class MockSecrets:
            @staticmethod
            def get_secret(secret_name):
                return {secret_name: None}
        secrets = MockSecrets()

    # Tenta import relativo (quando importado como módulo) ou absoluto (quando executado diretamente)
    try:
        from .config_semantic_search import (
            chat_model_config,
            bedrock_model_config,
            required_columns,
            search_config,
            suggestion_prompt_template,
            vector_search_config,
        )
        from .bedrock_chat import BedrockChat
    except ImportError:
        from config_semantic_search import (
            chat_model_config,
            bedrock_model_config,
            required_columns,
            search_config,
            suggestion_prompt_template,
            vector_search_config,
        )
        from bedrock_chat import BedrockChat


class SemanticSearch:
    def __init__(self, df: pd.DataFrame):
        self.client = self._configure_vector_search_client()
        self.endpoint_name = vector_search_config['endpoint_name']
        self.index_table = vector_search_config['index_table']
        self.table = vector_search_config['table']
        self.books_index = self.client.get_index(
            endpoint_name=str(self.endpoint_name), index_name=str(self.index_table))
        self.df = self._load_data(df)

    def _configure_vector_search_client(self):
        runner = str(os.getenv("WHO_IS_RUNNING_THIS"))
        print(f"DEBUG: A variável WHO_IS_RUNNING_THIS está como: '{runner}'")
        host = os.getenv("DATABRICKS_HOST") # so vai existir dentro do endpoint mlflow
        print("HOST: ", host)

        # Se rodando localmente, configura com credenciais do .env
        if runner == "local" or (not host and runner not in ["ENDPOINT_NOTEBOOK", "ENDPOINT_MLFLOW"]):
            print("LOG: Running locally. Using credentials from .env file...")
            databricks_host = os.getenv("DATABRICKS_HOST")
            databricks_token = os.getenv("DATABRICKS_TOKEN")

            if not databricks_host or not databricks_token:
                raise ValueError(
                    "DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env file.\n"
                    "Copy .env.config to .env and fill in your credentials."
                )

            # Garante que o host tem https://
            if not databricks_host.startswith("https://"):
                databricks_host = f"https://{databricks_host}"

            return VectorSearchClient(
                workspace_url=databricks_host,
                personal_access_token=databricks_token,
                disable_notice=True
            )

        # Se rodando no ENDPOINT_MLFLOW (ECS), pega host e token das variáveis de ambiente
        if runner == "ENDPOINT_MLFLOW":
            print("LOG: Running in ENDPOINT_MLFLOW mode (ECS)...")
            databricks_host = os.getenv("DATABRICKS_HOST")
            databricks_token = os.getenv("DATABRICKS_TOKEN")

            if not databricks_host or not databricks_token:
                raise ValueError(
                    "DATABRICKS_HOST and DATABRICKS_TOKEN must be set in environment or Secrets Manager."
                )

            # Garante que o host tem https://
            if not databricks_host.startswith("https://"):
                databricks_host = f"https://{databricks_host}"

            print(f"LOG: Connecting to Databricks at {databricks_host}")
            return VectorSearchClient(
                workspace_url=databricks_host,
                personal_access_token=databricks_token,
                disable_notice=True
            )

        # Se rodando no ENDPOINT_NOTEBOOK (Databricks), usa dynamic_catalog
        if not host: # se está rodando localmente sem WHO_IS_RUNNING_THIS, pega do dynamic_catalog
            host = "https://"+str(dynamic_catalog.get_host())
        else:
            # Garante que o host tem https://
            if not host.startswith("https://"):
                host = f"https://{host}"

        # Se o host for prod, então muda o workspace_url do vector search
        if host == "https://"+str(env_config.DATABRICKS_URL_PRD):
            print("LOG: It seems like we are in prod.\n\
                  Changing the workspace_url for the vector search endpoint...")
            token_name = env_config.DATABRICKS_TOKEN_DEV # token de dev
            token = secrets.get_secret(token_name)[token_name]
            return VectorSearchClient(
                workspace_url="https://"+str(env_config.DATABRICKS_URL_DEV),
                personal_access_token=token)
        else:
            print("LOG: It seems like we are in dev (Databricks notebook).\n\
                  Using the default vector search configuration...")
            # Se não estiver em prod, então usa configuração automática (só funciona dentro do Databricks)
            return VectorSearchClient(disable_notice=True) # padrão
        
    def _load_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df, pd.DataFrame):
            raise ValueError(
                "A Pandas DataFrame was expected, but the input came as {}".format(type(df)))

        # Seleciona somente as colunas necessárias e trata valores faltantes
        df_filtered = (
            df[required_columns]
            .dropna(how='all')
            .applymap(lambda x: str(x).strip() if pd.notna(x) else '')
        )

        # Remove linhas completamente vazias após o strip
        df_filtered = df_filtered[df_filtered.apply(
            lambda row: any(row), axis=1)]

        return df_filtered

    def get_exact_matches(self, search_content: str) -> list:
        try:
            df = self.df

            # Escape de aspas simples e retirada de hífens
            escaped_term = search_content.replace(
                "'", "''").replace("-", "").lower()

            # Remocao de hifens e lowerizacao
            for col in required_columns:
                df[col] = df[col].fillna("").astype(str)

            # Filtro
            mask = (
                (df['title'].str.contains(escaped_term, na=False)) |
                (df['authors'].str.contains(escaped_term, na=False)) |
                (df['isbn'] == escaped_term) |
                (df['isbn_digital'] == escaped_term)
            )
            filtered = df[mask].head(search_config['exact_match_limit'])

            exact_matches = []
            for _, row in filtered.iterrows():
                exact_matches.append({
                    'uuid': row['uuid'],
                    'title': row['title'],
                    'authors': row['authors'],
                    'score': search_config['exact_match_score'],
                    'method': 'exact'
                })

            return exact_matches

        except Exception as e:
            print(f"ERROR: Error in the exact search: {e}")
            return []

    def get_semantic_results(self, suggestion: str, num_results: int, score_threshold: float) -> list:
        thresholds = [score_threshold, 0.6, 0.5]
        for threshold in thresholds:
            results = self.books_index.similarity_search(
                query_text=suggestion,
                columns=required_columns,
                num_results=num_results,
                query_type="HYBRID",
                score_threshold=threshold
            )
            if results['result']['row_count'] > 0:
                columns = [col['name']
                           for col in results['manifest']['columns']]
                semantic_data = [
                    {
                        'uuid': row[columns.index('uuid')],
                        'title': row[columns.index('title')],
                        'authors': row[columns.index('authors')],
                        'score': row[columns.index('score')],
                        'method': 'semantic'
                    }
                    for row in results['result']['data_array']
                ]
                return semantic_data
            else:
                print(
                    f"LOG: No result with the {threshold} threshold, changing...")

        print("LOG: No semantic results found at any threshold.")
        return []

    def get_similar_books(self, search_content: str, suggestion: str) -> dict:
        num_results = search_config['num_results']
        score_threshold = search_config['score_threshold']

        # 1. Busca exata primeiro
        exact_matches = self.get_exact_matches(search_content)

        # 2. Busca semântica com thresholds dinamicos
        semantic_results = self.get_semantic_results(
            suggestion, num_results, score_threshold)

        # 3. Combina os resultados
        combined_results = exact_matches + semantic_results

        # 4. Ordena resultados por score e retira duplicatas
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        seen = set()
        unique_results = [x for x in combined_results if x["uuid"]
                          not in seen and not seen.add(x["uuid"])]

        return unique_results

    def generate_suggestion(self, search_content: str, provider: str = None) -> dict:
        # Determina o provider a ser usado
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "databricks").lower()

        prompt = suggestion_prompt_template.format(search_content=search_content)

        # Tenta usar o provider especificado
        if provider == "bedrock":
            try:
                print(f"LOG: Using AWS Bedrock for suggestion generation...")
                chat_model = BedrockChat(
                    model_id=bedrock_model_config.get('model_id'),
                    temperature=bedrock_model_config['temperature'],
                    max_tokens=bedrock_model_config['max_tokens'],
                    region_name=bedrock_model_config.get('region_name')
                )
                response = chat_model.invoke(prompt)
                print(f"LOG: ✓ AWS Bedrock suggestion generated successfully")
                return {
                    'suggestion': response.content,
                    'provider': 'bedrock',
                    'error': None,
                    'used_fallback': False
                }
            except Exception as e:
                error_msg = f"AWS Bedrock error: {e}"
                print(f"\n{'='*80}")
                print(f"WARNING: AWS Bedrock FAILED - Using original search text as fallback")
                print(f"ERROR: {error_msg}")
                print(f"{'='*80}\n")
                return {
                    'suggestion': search_content,
                    'provider': 'bedrock',
                    'error': error_msg,
                    'used_fallback': True
                }

        else:  # databricks 
            try:
                print(f"LOG: Using Databricks for suggestion generation...")
                chat_model = ChatDatabricks(
                    endpoint=chat_model_config['endpoint'],
                    temperature=chat_model_config['temperature'],
                    max_tokens=chat_model_config['max_tokens']
                )
                response = chat_model.invoke(prompt)
                print(f"LOG: ✓ Databricks suggestion generated successfully")
                return {
                    'suggestion': response.content,
                    'provider': 'databricks',
                    'error': None,
                    'used_fallback': False
                }
            except Exception as e:
                error_msg = f"Databricks error: {e}"
                print(f"\n{'='*80}")
                print(f"WARNING: Databricks FAILED - Using original search text as fallback")
                print(f"ERROR: {error_msg}")
                print(f"{'='*80}\n")
                return {
                    'suggestion': search_content,
                    'provider': 'databricks',
                    'error': error_msg,
                    'used_fallback': True
                }

    def search(self, search_content, provider: str = None) -> dict:
        bugsnag.notify(Exception("Teste bugsnag model_2 dev"))
        try:
            # Validação e extração do valor de busca
            if isinstance(search_content, str) and search_content.strip():
                search_value = search_content.strip()

            elif isinstance(search_content, dict) and search_content:
                search_value = list(search_content.values())[0]

            else:
                return {"success": False,
                        "results": [],
                        "error": "ERROR: Invalid input. Provide a non-empty string or dict."}

            # Executa a busca semântica com o provider escolhido
            suggestion_result = self.generate_suggestion(search_value, provider=provider)
            results = self.get_similar_books(search_value, suggestion_result['suggestion'])

            # Log adicional se usou fallback
            if suggestion_result.get('used_fallback'):
                print(f"WARNING: Search using FALLBACK mode - results may be less accurate")
                print(f"         Original text: '{search_value}'")
                print(f"         LLM refinement failed, using original text for vector search")

            return {
                "success": True,
                "results": results,
                "llm_provider": suggestion_result['provider'],
                "llm_suggestion": suggestion_result['suggestion'],
                "llm_error": suggestion_result['error'],
                "llm_used_fallback": suggestion_result.get('used_fallback', False)
            }

        except Exception as e:
            return {"success": False,
                    "results": [],
                    "error": f"ERROR: Search failed - {str(e)}"}
