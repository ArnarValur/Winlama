# ollama_client.py
from wsgiref.util import request_uri

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
            if not (self.base_url.startswith("http://") or self.base_url.startswith("https://")):
                raise requests.exceptions.MissingSchema(f"URL scheme (http/https) is missing from base_url: {self.base_url}")
            url = f"{self.base_url.rstrip('/')}/api/tags"

            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            models = data.get('models', [])
            #print(f"Models: {models}")
            model_names = [model['name'] for model in models]
            return model_names
        except requests.exceptions.MissingSchema as e:
            print(f"OllamaClient: Critical URL error in get_models - {e}")
            raise ValueError(f"Invalid URL to get_models: {e}. Ensure URL includes 'http://' or 'https://'.") from e
        except requests.exceptions.ConnectionError as e:
            print(f"OllamaClient: Connection error in get_models - {e}")
            raise ConnectionError("Failed to connect to Ollama server while fetching models.") from e
        except requests.exceptions.HTTPError as e:
            print(f"OllamaClient: HTTP error in get_models - {e.response.status_code} - {e.response.text}")
            raise ValueError(f"HTTP error {e.response.status_code} from Ollama server while fetching models") from e
        except json.JSONDecodeError as e:
            print(f"OllamaClient: JSON decoding error in get_models - {e}")
            raise ValueError("Failed to decode JSON response while fetching models.") from e
        except Exception as e:
            print(f"OllamaClient: An unexpected error occurred in get_models - {e}")
            raise Exception("An unexpected error occurred while fetching models.") from e

    def generate_response(self, model_name, prompt, stream=False, context=None):
        """ Generate a response from the Ollama server using the specified model.
        Args:
            :param model_name: The name of the model to use for generation.
            :param prompt: The input prompt for the model.
            :param stream: Whether to stream the response. Defaults to False.
            :param context: Additional context for the model. Defaults to None.
            :return: The generated response.
        """
        if stream:
            # TODO: Implement streaming response
            raise NotImplementedError("Streaming responses are not implemented yet.")

        try:
            url = f"{self.base_url.rstrip('/')}/api/generate"
            payload = {
                'model': model_name,
                'prompt': prompt,
                'stream': False
            }
            if context: # Ollama docs say context will be deprecated, find out why and other solution?
                payload['context'] = context

            print(f"OllamaClient: Sending payload to {url}: {{payload}}")

            # Timeout for requests
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            # The response from /api/generate when steam is False is a single Json object.
            response_data = response.json()
            print(f"OllamaClient: Response from server: {response_data}") # Debugging

            # The text response is in the "response" key, it also returns a "context" for a follow-up messages.
            return response_data.get("response", ""), response_data.get("context")

        except requests.exceptions.ConnectionError as e:
            print(f"OllamaClient: Connection error in generate_response - {e}")
            raise ConnectionError("Failed to connect to Ollama server for response generation.") from e
        except requests.exceptions.Timeout as e:
            print(f"OllamaClient: Timeout error in generate_response - {e}")
            raise TimeoutError("Request to Ollama times out.") from e
        except requests.exceptions.HTTPError as e:
            print(f"OllamaClient: HTTP error in generate_response - {e.response.status_code} - {e.response.text}")
            # Debug inspection:
            error_message = f"Http error {e.response.status_code} from Ollama server"
            try:
                ollama_error = e.response.json().get('error')
                if ollama_error:
                    error_message += f": Details: {ollama_error}"
            except json.JSONDecodeError:
                pass
            raise ValueError(error_message) from e
        except json.JSONDecodeError as e:
            print(f"OllamaClient: JSON decoding error in generate_response - {e}")
            print(f"OllamaClient: Raw response from server: {response.text}")
            raise ValueError("Failed to decode JSON response from Ollama during generation.") from e
        except Exception as e:
            print(f"OllamaClient: An unexpected error occurred in generate_response - {e}")
            raise Exception("An unexpected error occurred while generating response.") from e