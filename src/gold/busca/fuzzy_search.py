import os
import sys
from pathlib import Path
from typing import Any, Dict, List
# sys.path.append(str((Path.cwd() / Path('../' * 4)).resolve()))

import pandas as pd
from rapidfuzz import fuzz
import bugsnag

runner = str(os.getenv("WHO_IS_RUNNING_THIS"))
if (runner=="ENDPOINT_NOTEBOOK") or (runner=="ENDPOINT_MLFLOW"):
    from model.config_fuzzy_search import MAX_RESULTS, field_config, required_columns
else: # teste local
    from config_fuzzy_search import MAX_RESULTS, field_config, required_columns
    

class FuzzySearch:
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa a classe FuzzySearch com um DataFrame.

        Args:
            df (pd.DataFrame): DataFrame contendo os dados para busca fuzzy.
                               Deve conter as colunas obrigatórias: 'title', 'authors', 'isbn'.

        Raises:
            ValueError: Se o DataFrame não contiver as colunas obrigatórias ou for inválido.
        """
        self.df = self._load_data(df)

    def _load_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida e filtra o DataFrame com as colunas obrigatórias: 'title', 'authors', 'isbn'.

        Args:
            df (pd.DataFrame): DataFrame de entrada para validação e filtragem.

        Returns:
            pd.DataFrame: DataFrame filtrado e limpo, contendo apenas as colunas necessárias
                          com valores nulos tratados e linhas vazias removidas.

        Raises:
            ValueError: Se as colunas obrigatórias não existirem ou df for inválido.
        """
        if not isinstance(df, pd.DataFrame):
            raise ValueError(
                "Expecting a pd.DataFrame, but received: {}".format(type(df)))

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

    def calculate_score(self, row: pd.Series, selected_fields: Dict[str, str]) -> Dict[str, Any]:
        """
        Calcula o score de similaridade entre uma linha do DataFrame e os campos selecionados.

        Args:
            row (pd.Series): Linha do DataFrame para comparação.
            selected_fields (Dict[str, str]): Dicionário com os campos selecionados para busca,
                                               onde a chave é o nome do campo e o valor é o texto de busca.

        Returns:
            Dict[str, Any]: Dicionário contendo:
                - 'score' (float): Score total ponderado (0.0 a 1.0)
                - 'field_scores' (Dict[str, float]): Scores individuais por campo
                - 'criteria' (bool): Se todos os critérios mínimos foram atendidos
        """
        field_scores = {}
        weighted_score = 0.0
        total_weight = 0.0
        all_criteria_met = True

        for key, cfg in field_config.items():
            if key not in selected_fields:
                continue

            query = selected_fields[key].strip()
            text = row.get(cfg.get("attr", key), "").strip()
            ratio = fuzz.partial_ratio(text, query) / 100
            field_scores[key] = ratio

            if key == "isbn":
                if ratio == cfg["min_ratio"]:
                    return {"score": 1.0, "field_scores": field_scores, "criteria": True}
            else:
                if ratio >= cfg["min_ratio"]:
                    weighted_score += ratio * cfg["weight"]
                    total_weight += cfg["weight"]
                else:
                    all_criteria_met = False

        score = (weighted_score /
                 total_weight) if all_criteria_met and total_weight > 0 else 0.0

        return {
            "score": score,
            # "field_scores": field_scores,
            "criteria": all_criteria_met
        }

    def search_by_fields(self, selected_fields) -> List[Dict[str, Any]]:
        """
        Executa a busca fuzzy com base nos campos específicos.

        Args:
            selected_fields (Dict[str, str]): Dicionário com os campos selecionados para busca,
                                               onde a chave é o nome do campo e o valor é o texto de busca.

        Returns:
            List[Dict[str, Any]]: Lista de dicionários com resultados ordenados por score decrescente.
                                  Cada resultado contém: uuid, title, authors,
                                  score, e method.
                                  Limitado ao número máximo definido em MAX_RESULTS.
        """
        bugsnag.notify(Exception("Teste bugsnag model_1 dev"))
        results = []
        valid = False

        for _, row in self.df.iterrows():

            score_data = self.calculate_score(row, selected_fields)

            if score_data["criteria"] and score_data["score"] > 0:
                valid = True
                results.append({
                    "uuid": row['uuid'],
                    "title": row['title'],
                    "authors": row['authors'],
                    "score": score_data["score"],
                    "method": "fuzzy"
                })

        results.sort(key=lambda x: x["score"], reverse=True)

        return {"success": valid,
                "results": results[:MAX_RESULTS]}

    def search_by_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executa uma busca fuzzy usando uma única string de consulta em todos os campos.

        Args:
            query (str): String de busca que será comparada com todos os campos disponíveis
                        (title, authors, isbn).

        Returns:
            List[Dict[str, Any]]: Lista de dicionários com resultados ordenados por score decrescente.
                                 Cada resultado contém: uuid, title, authors, isbn_digital,
                                 score, field_scores e method.
                                 Limitado ao número máximo definido em MAX_RESULTS.
                                 Retorna apenas resultados onde pelo menos um campo atende
                                 ao critério mínimo de similaridade.
        """
        bugsnag.notify(Exception("Teste bugsnag model_1 dev"))
        results = []
        success = False

        attr_config_key = {
            "title": "titulo",
            "authors": "autores",
            "isbn": "isbn"
        }

        for _, row in self.df.iterrows():
            scores = {}
            valid = False

            for attr, key in attr_config_key.items():
                text = getattr(row, attr, "").strip()
                ratio = fuzz.partial_ratio(text, query) / 100
                scores[attr] = ratio

                if ratio >= field_config[key]["min_ratio"]:
                    valid = True

            if valid:
                success = True
                results.append({
                    "uuid": row['uuid'],
                    "title": row['title'],
                    "authors": row['authors'],
                    "score": sum(scores.values()) / len(scores),
                    "method": "fuzzy_query"
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return {"success": success,
                "results": results[:MAX_RESULTS]}
