# Configurações das tabelas
table_ebooks_search = "bronze_mb_dev.busca_avancada.ebooks_search"
output_csv = "./books_search.csv"

# Configurações de busca
MAX_RESULTS = 50
required_columns = ["title", "authors", "isbn", "uuid", "isbn_digital"]


field_config = {
    "titulo": {"attr": "title", "weight": 0.6, "min_ratio": 0.8},
    "autores": {"attr": "authors", "weight": 0.4, "min_ratio": 0.8},
    "isbn": {"attr": "isbn", "weight": 1.0, "min_ratio": 1.0}
}

# Configurações de atualização
update_books = {
    "brm_books": "bronze_mb_dev.odoo_prd.brm_book",
    "filter_brm": ["active", "waiting_for_epub"],
    "new_columns": ["id", "edition", "edition_year", "imprint_id", "uuid", "isbn", "isbn_digital", "title", "subtitle", "organizer", "illustrator", "description", "authors", "info"],
    "string_columns" : ["uuid", "isbn", "isbn_digital", "title", "subtitle", "organizer", "illustrator", "description", "authors", "info"]

}

# Configurações do Vector Search
vs_config = {
    "endpoint_name": "my_books_endpoint",
    "index_name": "gold_mb_dev.busca_avancada.my_books_search_index",
    "embedding_model_endpoint_name": "databricks-bge-large-en",
    "source_table_name": table_ebooks_search,
    "pk": "uuid",
    "emb_column": "info"
}
