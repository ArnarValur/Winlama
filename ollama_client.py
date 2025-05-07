import requests
import json

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def get_models(self):
        """
        Fetches the list of available models from the Ollama Server.
        Returns a list of model names.
        Raises exceptions for connection or HTTP errors.
        :return: List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = data.get('models', [])
            model_names = [model['name'] for model in models]
            return model_names
        except requests.exceptions.ConnectionError as e:
            print(f"OllamaClient: Connection error - {e}")
            raise ConnectionError("Failed to connect to Ollama server.") from e
        except requests.exceptions.HTTPError as e:
            print(f"OllamaClient: HTTP error - {e}")
            raise ValueError("Failed to fetch models: {e.response.status_code}") from e
        except json.JSONDecodeError as e:
            print(f"OllamaClient: JSON decoding error - {e}")
            raise ValueError("Failed to decode JSON response.") from e
        except Exception as e:
            print(f"OllamaClient: Unknown error - {e}")
            raise Exception("An unknown error occurred.") from e
