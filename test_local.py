"""
Script de teste para execução local do sistema de busca avançada.
Executa a função consolidation_function com dados de exemplo.
"""
import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Define ambiente como local
os.environ["WHO_IS_RUNNING_THIS"] = "local"

import pandas as pd
from gold.busca.main import consolidation_function

def test_busca_texto_livre():
    """Teste de busca por texto livre com AMBOS os providers"""
    print("=" * 80)
    print("TESTE 1: Busca por texto livre - COMPARANDO DATABRICKS vs AWS BEDROCK")
    print("=" * 80)

    data = {
        'searchQuery': 'Maria da Penha',
        'selectedFields': {
            'titulo': '',
            'autores': '',
            'assunto': '',
            'isbn': ''
        },
       'userCatalogs': [
            "538f6227-897a-4a58-8e31-a5fa5b3f9843",
            "081c27c7-d1dc-425e-ba9a-f838df4187ee",
            "68b15a1f-615f-4751-8239-e929f11fa0a8",
            "487eb979-ed08-4ed0-ab3a-9bad0d40420d",
            "9e29e343-8f08-4da6-b61b-ba449c35d766",
            "4a85e11c-3b6d-4760-8829-d9b49d59a4e9",
            "ffa7d139-73bd-4180-b1c5-6844eda14048",
            "fb8905ba-6ce4-4716-9637-d209aeda365a",
            "ea937fd9-454a-4369-bac4-a94db7cbff9d",
            "4bc4dc85-dac6-4556-9008-949e691b0957",
            "f5b33ddb-aab3-44e6-99e2-eaf1d19951ad",
            "1acfd238-a4b4-4150-ba27-b11862c9b539",
            "8f6ec6c1-dd31-4bd1-8d71-616510c6f3fe",
            "7f5a012b-1eab-4e10-b359-c0a8153c0554",
            "8d815eb9-50ef-48f3-ba3d-319a0f420d29",
            "e375d6f8-bf23-4303-8d0e-bd29203d1ef9",
            "69729166-75f1-4993-9c02-fe9b860182e5",
            "c3126820-7665-4ac9-a93b-fb3d8ed3eed0",
            "d0e1e7b7-ba2e-4385-b296-d6f3ec00ab7c",
            "f13ea59c-604d-4903-8b78-8f442f9229de",
            "a9fe6285-3cfc-4521-941a-e5da11b8291a",
            "9d8369e5-0877-465d-ba05-d3efb2a48a67"
        ]
    }

    # Carrega o CSV
    csv_path = Path(__file__).parent / "src" / "gold" / "busca" / "books_search.csv"
    if not csv_path.exists():
        print(f"ERRO: Arquivo CSV não encontrado em {csv_path}")
        return

    file_csv = pd.read_csv(csv_path, encoding="utf-8")
    print(f"CSV carregado: {len(file_csv)} livros\n")

    # Testa com DATABRICKS primeiro
    print("\n" + "=" * 80)
    print("TESTE COM DATABRICKS")
    print("=" * 80)
    os.environ["LLM_PROVIDER"] = "databricks"
    result_databricks = consolidation_function(data, file_csv, local=True)

    print(f"\n✓ Resultado Databricks:")
    print(f"  Success: {result_databricks.get('success')}")
    print(f"  Total de resultados: {len(result_databricks.get('results', []))}")

    if result_databricks.get('results'):
        print(f"\n  Primeiros 3 resultados (DATABRICKS):")
        for i, book in enumerate(result_databricks['results'][:3], 1):
            print(f"\n  {i}. {book.get('title')}")
            print(f"     Autor: {book.get('authors')}")
            print(f"     Score: {book.get('score'):.2f}")
            print(f"     Método: {book.get('method')}")

    if result_databricks.get('error'):
        print(f"\n  ⚠ Erro Databricks: {result_databricks.get('error')}")

    # Testa com AWS BEDROCK
    print("\n\n" + "=" * 80)
    print("TESTE COM AWS BEDROCK")
    print("=" * 80)
    os.environ["LLM_PROVIDER"] = "bedrock"
    result_bedrock = consolidation_function(data, file_csv, local=True)

    print(f"\n✓ Resultado AWS Bedrock:")
    print(f"  Success: {result_bedrock.get('success')}")
    print(f"  Total de resultados: {len(result_bedrock.get('results', []))}")

    if result_bedrock.get('results'):
        print(f"\n  Primeiros 3 resultados (AWS BEDROCK):")
        for i, book in enumerate(result_bedrock['results'][:3], 1):
            print(f"\n  {i}. {book.get('title')}")
            print(f"     Autor: {book.get('authors')}")
            print(f"     Score: {book.get('score'):.2f}")
            print(f"     Método: {book.get('method')}")

    if result_bedrock.get('error'):
        print(f"\n  ⚠ Erro AWS Bedrock: {result_bedrock.get('error')}")

    # Comparação final
    print("\n\n" + "=" * 80)
    print("COMPARAÇÃO DATABRICKS vs AWS BEDROCK")
    print("=" * 80)
    print(f"Total resultados Databricks: {len(result_databricks.get('results', []))}")
    print(f"Total resultados AWS Bedrock: {len(result_bedrock.get('results', []))}")
    print("=" * 80)


def test_busca_por_campos():
    """Teste de busca por campos específicos"""
    print("\n\n" + "=" * 60)
    print("TESTE 2: Busca por campos específicos (título)")
    print("=" * 60)

    data = {
        'searchQuery': '',
        'selectedFields': {
            'titulo': 'Python',
            'autores': '',
            'assunto': '',
            'isbn': ''
        },
        'userCatalogs': [
            "538f6227-897a-4a58-8e31-a5fa5b3f9843",
            "081c27c7-d1dc-425e-ba9a-f838df4187ee"
        ]
    }

    csv_path = Path(__file__).parent / "src" / "gold" / "busca" / "books_search.csv"
    file_csv = pd.read_csv(csv_path, encoding="utf-8")

    result = consolidation_function(data, file_csv, local=True)

    print(f"\nResultado:")
    print(f"  Success: {result.get('success')}")
    print(f"  Total de resultados: {len(result.get('results', []))}")

    if result.get('results'):
        print(f"\nPrimeiros 3 resultados:")
        for i, book in enumerate(result['results'][:3], 1):
            print(f"\n  {i}. {book.get('title')}")
            print(f"     Autor: {book.get('authors')}")
            print(f"     Score: {book.get('score'):.2f}")
            print(f"     Método: {book.get('method')}")


if __name__ == "__main__":
    print("\nIniciando testes de busca avançada local\n")

    # Verifica se o .env existe
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("Arquivo .env não encontrado!")
        print("   Copie .env.config para .env e configure suas credenciais Databricks")
        print("   Comando: cp .env.config .env")
        print("\n   Configure no .env:")
        print("     DATABRICKS_HOST=seu-workspace.cloud.databricks.com")
        print("     DATABRICKS_TOKEN=dapi1234567890abcdef")
        sys.exit(1)

    try:
        test_busca_texto_livre()
        test_busca_por_campos()
        print("\n\nTestes concluídos com sucesso")
    except Exception as e:
        print(f"\n\nErro durante os testes: {e}")
        import traceback
        traceback.print_exc()
