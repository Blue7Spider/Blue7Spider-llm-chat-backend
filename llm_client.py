import httpx
import json
from typing import AsyncGenerator
from app import settings

class ExternalLanguageModelClient:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions" # Példa Groq/Gemini-szerű végpontra
        self.timeout_seconds = 30.0

    async def stream_chat_completion(
        self, 
        system_instruction: str, 
        conversation_history: list[dict], 
        generation_config: dict
    ) -> AsyncGenerator[str, None]:
        """
        Aszinkron HTTP klienssel kezelt szerveroldali esemény-stream (SSE) hívás.
        """
        # Payload összeállítása tiszta struktúrában
        formatted_messages = [{"role": "system", "content": system_instruction}]
        formatted_messages.extend(conversation_history)

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key.get_secret_value()}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama3-8b-8192",
            "messages": formatted_messages,
            "temperature": generation_config.get("temperature", 0.7),
            "top_p": generation_config.get("top_p", 0.9),
            "max_tokens": generation_config.get("max_output_tokens", 1024),
            "stream": True
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            async with client.stream("POST", self.api_url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    yield f"Hiba történt az LLM szolgáltatónál: {response.status_code}"
                    return

                async for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_content = line[6:]
                        if data_content.strip() == "[DONE]":
                            break
                        try:
                            json_chunk = json.loads(data_content)
                            token_chunk = json_chunk["choices"][0]["delta"].get("content", "")
                            if token_chunk:
                                yield token_chunk
                        except (json.JSONDecodeError, KeyError):
                            continue