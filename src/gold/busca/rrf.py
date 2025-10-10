import pandas as pd
from collections import defaultdict
import os
from typing import List

class RRF:
    @staticmethod
    def rrf_fusion(systems: list[list[dict]], k: int = 60) -> list:
        """
        Aplica o algoritmo RRF (Reciprocal Rank Fusion) a VARIOS sistemas de busca.
        
        Args:
            systems (list[dict]): Lista de sistemas, cada um com a estrutura:
            {'success': bool, 'results': list[dict]}.
            k (int): Parâmetro de suavização do RRF.
            
        Returns:
            list: Lista de livros ordenada por RRF score.
        """
        
        rrf_scores = defaultdict(lambda: {"rrf": 0, "best_book": None})
        systems_processed = 0
        print("LOG: Systems: ", systems)
        for system in systems:
            # Verifica se o sistema é válido e tem resultados
            
            if (system.get("success") and 
                isinstance(system.get("results"), list) and 
                len(system.get("results")) > 0):
                
                systems_processed += 1
                print(f"DEBUG: Sistema válido com {len(system['results'])} resultados")
                
                for rank, book in enumerate(system["results"]):
                    if isinstance(book, dict) and book.get("uuid"):
                        uuid = book.get("uuid")
                        rrf_score = 1 / (k + rank + 1)  # +1 porque enumerate começa em 0
                        rrf_scores[uuid]["rrf"] += rrf_score
                        
                        print(f"DEBUG: Livro {uuid} recebeu RRF score {rrf_score} (rank {rank})")

                        # Atualiza o livro com maior score se necessário
                        if (rrf_scores[uuid]["best_book"] is None or 
                            book.get("score", 0) > rrf_scores[uuid]["best_book"].get("score", 0)):
                            rrf_scores[uuid]["best_book"] = book
            else:
                print(f"DEBUG: Sistema ignorado (sem sucesso ou sem resultados): {system}")
                continue
        
        print(f"DEBUG: Total de sistemas processados: {systems_processed}")
        
        # Se nenhum sistema foi processado com sucesso, retorna lista vazia
        if systems_processed == 0:
            print("DEBUG: Nenhum sistema válido encontrado")
            return []
        
        # Ordena por RRF score (maior primeiro) e depois por score original como desempate
        sorted_books = sorted(
            rrf_scores.items(), 
            key=lambda x: (x[1]["rrf"], x[1]["best_book"].get("score", 0)), 
            reverse=True
        )
        
        books_from_rrf = [item[1]["best_book"] for item in sorted_books]
        
        print(f"DEBUG: RRF retornando {len(books_from_rrf)} livros únicos")
        return books_from_rrf

    @staticmethod
    def filter_books_by_user_catalogs(df: pd.DataFrame, user_catalogs: List[str]) -> pd.DataFrame:
        """
        Filtra o DataFrame de livros baseado nos catálogos que o usuário tem acesso.
        
        Args:
            df (pd.DataFrame): DataFrame com os dados dos livros (deve conter coluna 'brm_catalog_id')
            user_catalogs (List[str]): Lista de IDs dos catálogos que o usuário tem acesso
        
        Returns:
            pd.DataFrame: DataFrame filtrado apenas com livros dos catálogos autorizados
        """
        if not user_catalogs:
            # Se o usuário não tem catálogos, retorna DataFrame vazio
            return pd.DataFrame(columns=df.columns)

        # Filtra apenas livros dos catálogos autorizados
        filtered_df = df[df['catalog_uuid'].isin(user_catalogs)].drop_duplicates(subset='brm_book_id')
        
        return filtered_df

    @staticmethod
    def filter_semantic_results_by_user_catalogs(res_search: dict, filtered_csv: pd.DataFrame) -> dict:
        """
        Filtra os resultados semânticos retornando apenas aqueles cujo UUID está presente no catálogo do usuário.

        Parâmetros:
            res_search (dict): Dicionário com os resultados da busca livre
            filtered_csv (pd.DataFrame): DataFrame do pandas contendo os livros dos catálogos que o usuário tem acesso

        Retorna:
            dict: Um dicionário indicando sucesso ou falha e os resultados filtrados.
        """
        
        # Obtém o conjunto de UUIDs do DataFrame, convertendo para string e minúsculas para garantir comparação
        uuids = set(filtered_csv["uuid"].astype(str).str.lower())

        # Filtra os resultados da busca, mantendo apenas aqueles cujo UUID está no conjunto de UUIDs do usuário
        kept = [r for r in res_search.get("results", []) if str(r.get("uuid", "")).lower() in uuids]

        # Se não encontrar nenhum resultado, retorna erro e lista vazia
        if not kept:
            return {
                "success": False,
                "error": "Usuário não tem acesso a nenhum catálogo ou catálogos não encontrados",
                "results": []
            }

        # Caso contrário, retorna sucesso e os resultados filtrados
        return {"success": True, "results": kept}
