# from pathlib import Path
# import sys
# sys.path.append(str((Path.cwd()/Path('../' * 6)).resolve()))
import bugsnag
import os

runner = str(os.getenv("WHO_IS_RUNNING_THIS"))
if runner=="ENDPOINT_NOTEBOOK":
    from model.fuzzy_search import *
    from model.semantic_search import *
    from model.rrf import *
    from utils.bugsnag_utils import bugsnag_notify
elif runner=="ENDPOINT_MLFLOW":
    from model.fuzzy_search import *
    from model.semantic_search import *
    from model.rrf import *
    from bugsnag_utils import bugsnag_notify
else: # local
    from fuzzy_search import *
    from semantic_search import *
    from rrf import *
    from utils.bugsnag_utils import bugsnag_notify

bugsnag_notify.configure_bugsnag()

def consolidation_function(data, file_csv, local):
    """
    Consolida buscas em catálogos de livros com base em campos selecionados ou consulta textual.
    Retorna resultados fuzzy, semânticos ou mensagem de erro.
    """
    bugsnag.notify(Exception("Teste bugsnag cons dev"))
    rrf_functions = RRF() 

    # Validação de entrada
    if not isinstance(data, dict):
        return {"success": False, 
                "results": [], 
                "error": "Invalid data type. Expected a dictionary."}

    selected_fields = data.get("selectedFields", {})
    search_query = (data.get("searchQuery") or "").strip()
    user_catalogs = data.get("userCatalogs", [])

    # Filtra o DataFrame pelos catálogos do usuário
    filtered_csv = rrf_functions.filter_books_by_user_catalogs(file_csv, user_catalogs)
    #filtered_csv = filter_books_by_user_catalogs(file_csv, user_catalogs)

    if filtered_csv.empty:
        return {
            "success": False,
            "results": [],
            "error": "No books found for the specified user. Please check their catalog subscription.",
        }

    semantic_searcher = SemanticSearch(file_csv)
    #semantic_searcher = SemanticSearch(filtered_csv)
    fuzzy_searcher = FuzzySearch(filtered_csv)
    
    filled_fields = {k: v for k, v in selected_fields.items() if v}

    # Busca por campos selecionados preenchidos
    # Se não achar, retorna vazio e nao continua
    # o processamento - só se for texto livre
    if filled_fields:
        if set(filled_fields).issubset(field_config):
            fuzzy_results = fuzzy_searcher.search_by_fields(filled_fields)
            if fuzzy_results.get("success"):
                return fuzzy_results
            return {
                "success": False,
                "results": [],
                "error": "No books found for the specified filter.",
            }

        res_semantic = semantic_searcher.search(filled_fields)
        filtered_sem = rrf_functions.filter_semantic_results_by_user_catalogs(res_semantic, filtered_csv)
        #filtered_sem = filter_semantic_results_by_user_catalogs(res_semantic, filtered_csv)
        if not filtered_sem.get("success"):
            return filtered_sem
        return {"success": True,
                "results": res_semantic or []}

    # Busca por texto livre
    if search_query:
        semantic_results = semantic_searcher.search(search_query)
        fuzzy_results = fuzzy_searcher.search_by_query(search_query)

        filtered_semantic_results = rrf_functions.filter_semantic_results_by_user_catalogs(semantic_results, filtered_csv)
        filtered_fuzzy_results = rrf_functions.filter_semantic_results_by_user_catalogs(fuzzy_results, filtered_csv)
        rrf = rrf_functions.rrf_fusion([filtered_semantic_results, filtered_fuzzy_results])

        # filtered_semantic_results = filter_semantic_results_by_user_catalogs(semantic_results, filtered_csv)
        # filtered_fuzzy_results = filter_semantic_results_by_user_catalogs(fuzzy_results, filtered_csv)
        # rrf = rrf_fusion([filtered_semantic_results, filtered_fuzzy_results])

        rrf.sort(key=lambda x: x["score"], reverse=True) # ordenacao
        return {"success": bool(rrf), "results": rrf or []}

    # Nenhum critério de busca fornecido
    return {
        "success": False,
        "results": [],
        "error": "No search content provided. Please specify either selected fields or a search query.",
    }

# ======================== TESTE LOCAL =========================

# # # Para testar localmente, descomente esse bloco. 
# # # Lembre-se de comentá-lo ao fim dos testes.
# import pandas as pd
# data = {'searchQuery': 'Lei Maria da Penha',
#         'selectedFields': {
#             'titulo': '',
#             'autores': '',
#             'assunto': '',
#             'isbn': ''
#         },
#         'userCatalogs': [
#             "538f6227-897a-4a58-8e31-a5fa5b3f9843",
#             "081c27c7-d1dc-425e-ba9a-f838df4187ee",
#             "68b15a1f-615f-4751-8239-e929f11fa0a8",
#             "487eb979-ed08-4ed0-ab3a-9bad0d40420d",
#             "9e29e343-8f08-4da6-b61b-ba449c35d766",
#             "4a85e11c-3b6d-4760-8829-d9b49d59a4e9",
#             "ffa7d139-73bd-4180-b1c5-6844eda14048",
#             "fb8905ba-6ce4-4716-9637-d209aeda365a",
#             "ea937fd9-454a-4369-bac4-a94db7cbff9d",
#             "4bc4dc85-dac6-4556-9008-949e691b0957",
#             "f5b33ddb-aab3-44e6-99e2-eaf1d19951ad",
#             "1acfd238-a4b4-4150-ba27-b11862c9b539",
#             "8f6ec6c1-dd31-4bd1-8d71-616510c6f3fe",
#             "7f5a012b-1eab-4e10-b359-c0a8153c0554",
#             "8d815eb9-50ef-48f3-ba3d-319a0f420d29",
#             "e375d6f8-bf23-4303-8d0e-bd29203d1ef9",
#             "69729166-75f1-4993-9c02-fe9b860182e5",
#             "c3126820-7665-4ac9-a93b-fb3d8ed3eed0",
#             "d0e1e7b7-ba2e-4385-b296-d6f3ec00ab7c",
#             "f13ea59c-604d-4903-8b78-8f442f9229de",
#             "a9fe6285-3cfc-4521-941a-e5da11b8291a",
#             "9d8369e5-0877-465d-ba05-d3efb2a48a67"]}
# file_csv = pd.read_csv("./books_search.csv", encoding="utf-8")
# local = True
# # display(file_csv.head())
# consolidation_function(data, file_csv, local)