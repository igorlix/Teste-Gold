import os
import sys
import time
from typing import Any, Dict, List

# from pathlib import Path
# sys.path.append(str((Path.cwd() / Path('../' * 3)).resolve()))

import pandas as pd
from databricks.vector_search.client import VectorSearchClient
from databricks_langchain import ChatDatabricks
import bugsnag

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
    from dynamic_cat import env_config
    from aws_utils import secrets
    from model.config_semantic_search import (
        chat_model_config,
        required_columns,
        search_config,
        suggestion_prompt_template,
        vector_search_config,
    )
else: # teste local
    from utils.dynamic_cat import dynamic_catalog, env_config
    from utils.aws_utils import secrets
    from config_semantic_search import (
        chat_model_config,
        required_columns,
        search_config,
        suggestion_prompt_template,
        vector_search_config,
    )

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
        """
        Configura o VectorSearchClient baseado no host atual.
        O vector search endpoint só existe em dev, então se estiver
        em prod, precisa mudar o workspace_url.
        
        Returns:
            VectorSearchClient: Cliente configurado para o workspace apropriado
        """
        host = os.getenv("DATABRICKS_HOST") # so vai existir dentro do endpoint mlflow
        print("HOST: ", host)
        if not host: # se está rodando localmente, então vai retornar None
            host = "https://"+str(dynamic_catalog.get_host())

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
            print("LOG: It seems like we are in dev.\n\
                  Using the local vector search endpoint...")
            # Se não estiver em prod, então usa configuração automática
            return VectorSearchClient(disable_notice=True) # padrão
        
    def _load_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida e filtra o DataFrame com as colunas obrigatórias: 'title', 'authors', 'isbn'.

        Returns:
            pd.DataFrame: DataFrame filtrado.

        Raises:
            ValueError: Se as colunas obrigatórias não existirem ou df for inválido.
        """
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
        """
        Busca correspondências exatas no título, autor ou ISBN
        usando o arquivo data.csv salvo na mesma pasta deste arquivo .py.
        Retorna lista de dicionários com os livros encontrados.
        """
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
        """
        Executa a busca semântica com thresholds progressivos.
        """

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
        """
        Combina busca exata (score > 1) com busca semântica.
        search_content: busca exata do usuário,
        suggestion: tratamento da LLM
        """

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

    def generate_suggestion(self, search_content: str) -> str:
        """
        Usa LangChain com configuração explícita de credenciais.
        """
        try:
            chat_model = ChatDatabricks(
                endpoint=chat_model_config['endpoint'],
                temperature=chat_model_config['temperature'],
                max_tokens=chat_model_config['max_tokens']
            )
            prompt = suggestion_prompt_template.format(
                search_content=search_content)

            response = chat_model.invoke(prompt)
            return response.content

        except Exception as e:
            print(f"WARNING: Error generating suggestion: {e}")
            return search_content

    def search(self, search_content) -> dict:
        """
        Executa busca semântica baseada em string ou dicionário de campos.

        Args:
            search_content: String de busca ou dicionário com campos preenchidos

        Returns:
            dict: Resultado da busca com success/error e lista de resultados
        """
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

            # Executa a busca semântica
            suggestion = self.generate_suggestion(search_value)
            results = self.get_similar_books(search_value, suggestion)

            return {"success": True,
                    "results": results}

        except Exception as e:
            return {"success": False,
                    "results": [],
                    "error": f"ERROR: Search failed - {str(e)}"}
