# Configurações do Databricks Vector Search
vector_search_config = {
    "endpoint_name": "recommendation_endpoint",
    "index_table": "gold_mb_dev.busca_avancada.ebooks_search_index",
    "table": "bronze_mb_dev.busca_avancada.ebooks_search"
}

# Configurações do modelo de chat Databricks
chat_model_config = {
    "endpoint": "databricks-claude-3-7-sonnet",
    "temperature": 0.3,
    "max_tokens": 150
}


bedrock_model_config = {
    # Modelos Claude bloqueados para Channel Program Accounts
    # Alternativas: "us.amazon.nova-lite-v1:0" (mais rápido/barato) ou "us.amazon.nova-pro-v1:0" (melhor qualidade)
    "model_id": "us.amazon.nova-pro-v1:0",
    "temperature": 0.3,
    "max_tokens": 150,
    "region_name": "us-east-2"  
}

# Configurações de busca
search_config = {
    "num_results": 50,
    "score_threshold": 0.75,
    "exact_match_limit": 50,
    "exact_match_score": 1.5
}

# Colunas obrigatórias do DataFrame
required_columns = ['uuid','title', 'authors', 'isbn', 'isbn_digital']

# Prompt template para geração de sugestões
suggestion_prompt_template = (
    "O usuário digitou '{search_content}' como termo de busca em uma biblioteca digital. "
    "Explique o possível significado deste termo e sugira uma forma mais eficaz e clara de "
    "expressar essa busca, resumindo sua sugestão em uma única frase."
)

