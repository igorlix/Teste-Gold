import os
import json
from typing import Optional
import boto3
from botocore.exceptions import ClientError


class BedrockChat:
    """
    AWS Bedrock requer o uso de Inference Profiles para modelos mais recentes.
    Exemplo de inference profiles:
    - us.amazon.nova-pro-v1:0 (Cross-region inference profile)
    - arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0
    """

    # Mapeamento de model IDs diretos para Inference Profiles
    MODEL_TO_INFERENCE_PROFILE = {
        "anthropic.claude-sonnet-4-20250514-v1:0": "us.anthropic.claude-sonnet-4-v1:0",
        "anthropic.claude-3-7-sonnet-20250219-v1:0": "us.anthropic.claude-3-7-sonnet-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0": "us.anthropic.claude-3-5-sonnet-v2:0",
    }

    def __init__(
        self,
        model_id: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 150,
        region_name: Optional[str] = None,
        bearer_token: Optional[str] = None
    ):
        raw_model_id = model_id or os.getenv("AWS_BEDROCK_MODEL_ID")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")

        # Token bearer (pode ser usado para autenticação adicional se necessário)
        self.bearer_token = bearer_token or os.getenv("AWS_BEARER_TOKEN_BEDROCK")

        if not raw_model_id:
            raise ValueError(
                "model_id must be specified or AWS_BEDROCK_MODEL_ID must be set in .env"
            )

        # Converte model ID direto para Inference Profile se necessário
        self.model_id = self._get_inference_profile(raw_model_id)
        if self.model_id != raw_model_id:
            print(f"LOG: Converted model ID '{raw_model_id}' to inference profile '{self.model_id}'")

        # Inicializa cliente boto3 para Bedrock Runtime
        # Usa credenciais do AWS CLI (aws configure)
        try:
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region_name
            )
            print(f"LOG: AWS Bedrock client initialized successfully (region: {self.region_name}, model: {self.model_id})")
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize AWS Bedrock client: {e}\n"
                "Make sure you have configured AWS credentials using 'aws configure'"
            )

    def _get_inference_profile(self, model_id: str) -> str:
        """
        Converte model ID direto para Inference Profile quando necessário.

        Args:
            model_id: Model ID direto ou Inference Profile

        Returns:
            str: Inference Profile correspondente ou model_id original
        """
        # Se já é um inference profile (começa com region prefix ou us.), retorna direto
        if model_id.startswith(("us.", "eu.", "ap.", "arn:aws:bedrock")):
            return model_id

        # Tenta mapear para inference profile
        if model_id in self.MODEL_TO_INFERENCE_PROFILE:
            return self.MODEL_TO_INFERENCE_PROFILE[model_id]

        # Se não encontrou mapeamento, retorna original (pode funcionar para modelos antigos)
        return model_id

    def invoke(self, prompt: str) -> 'BedrockResponse':
        try:
            # Detecta se é modelo Amazon Nova (usa Converse API) ou Claude (usa invoke_model)
            is_nova = 'nova' in self.model_id.lower()
            is_claude = 'claude' in self.model_id.lower() or 'anthropic' in self.model_id.lower()

            if is_nova:
                # Amazon Nova usa a API Converse com formato diferente
                response = self.client.converse(
                    modelId=self.model_id,
                    messages=[{
                        'role': 'user',
                        'content': [{'text': prompt}]
                    }],
                    inferenceConfig={
                        'maxTokens': self.max_tokens,  # maxTokens, não max_tokens
                        'temperature': self.temperature
                    }
                )

                # Extrai o texto da resposta do formato Converse
                content = response['output']['message']['content'][0]['text']
                return BedrockResponse(content=content, raw_response=response)

            elif is_claude:
                # Claude usa a API invoke_model com Messages API format
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })

                # Invoca o modelo (funciona tanto com inference profiles quanto model IDs diretos)
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=body,
                    contentType='application/json',
                    accept='application/json'
                )

                # Processa a resposta
                response_body = json.loads(response['body'].read())

                # Extrai o texto da resposta
                content = response_body.get('content', [{}])[0].get('text', '')

                return BedrockResponse(content=content, raw_response=response_body)

            else:
                # Fallback: tenta usar Converse API (padrão para novos modelos)
                response = self.client.converse(
                    modelId=self.model_id,
                    messages=[{
                        'role': 'user',
                        'content': [{'text': prompt}]
                    }],
                    inferenceConfig={
                        'maxTokens': self.max_tokens,
                        'temperature': self.temperature
                    }
                )

                content = response['output']['message']['content'][0]['text']
                return BedrockResponse(content=content, raw_response=response)

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']

            # Mensagem de erro mais detalhada para ValidationException
            if error_code == 'ValidationException' and 'inference profile' in error_message.lower():
                available_profiles = ", ".join(self.MODEL_TO_INFERENCE_PROFILE.values())
                raise RuntimeError(
                    f"AWS Bedrock API error ({error_code}): {error_message}\n"
                    f"Model ID '{self.model_id}' requires an inference profile.\n"
                    f"Available inference profiles: {available_profiles}\n"
                    f"Update your config to use an inference profile instead of direct model ID."
                )

            raise RuntimeError(
                f"AWS Bedrock API error ({error_code}): {error_message}"
            )
        except Exception as e:
            raise RuntimeError(f"Error invoking Bedrock model: {e}")


class BedrockResponse:

    def __init__(self, content: str, raw_response: dict):
        self.content = content
        self.raw_response = raw_response

    def __str__(self):
        return self.content

    def __repr__(self):
        return f"BedrockResponse(content='{self.content[:50]}...')"


# Testes básicos do módulo
if __name__ == "__main__":
    from dotenv import load_dotenv

    # Carrega variáveis de ambiente
    load_dotenv()

    print("=" * 60)
    print("Teste do módulo BedrockChat")
    print("=" * 60)

    try:
        # Inicializa o cliente
        chat = BedrockChat(
            temperature=0.3,
            max_tokens=150
        )

        # Teste de prompt
        test_prompt = "O usuário digitou 'python programming' como termo de busca. Sugira uma forma mais eficaz de expressar essa busca em uma única frase."

        print(f"\nPrompt: {test_prompt}")
        print("\nInvocando AWS Bedrock...")

        response = chat.invoke(test_prompt)

        print(f"\nResposta: {response.content}")
        print("\nTeste concluído com sucesso!")

    except Exception as e:
        print(f"\nErro no teste: {e}")
        import traceback
        traceback.print_exc()
