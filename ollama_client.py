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
        except requests.exceptions.Timeout as e:
            print(f"OllamaClient: Timeout error in get_models - {e}")
            raise TimeoutError("Request to Ollama timed out while fetching models.") from e
        except requests.exceptions.HTTPError as e:
            print(f"OllamaClient: HTTP error in get_models - {e.response.status_code} - {e.response.text}")
            raise ValueError(f"HTTP error {e.response.status_code} from Ollama server while fetching models") from e
        except json.JSONDecodeError as e:
            print(f"OllamaClient: JSON decoding error in get_models - {e}")
            raise ValueError("Failed to decode JSON response while fetching models.") from e
        except Exception as e:
            print(f"OllamaClient: An unexpected error occurred in get_models - {e}")
            raise Exception("An unexpected error occurred while fetching models.") from e

    def generate_response_stream(self, model_name, prompt, context=None):
        """ Generate a response from the Ollama server using the specified model, yielding parts of the response.
        Args:
            :param model_name: The name of the model to use for generation.
            :param prompt: The input prompt for the model.
            :param context: Previous conversation context (list of integers).
        Yields:
            dict: Parsed JSON objects from the Ollama stream.
                Each object typically contains 'response' (a token/chunk of text)
                and 'done' (boolean). The final object when done=true will
                contain the full context and other summary info.
        """
        try:
            url = f"{self.base_url.rstrip('/')}/api/generate"
            payload = {
                'model': model_name,
                'prompt': prompt,
                'stream': True
            }
            if context: # Ollama docs say context will be deprecated, find out why and other solution?
                payload['context'] = context

            print(f"OllamaClient: Sending payload to {url}: {{payload}}")

            with requests.post(url, json=payload, stream=True, timeout=300) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        try:
                            json_line = line.decode('utf-8')
                            chunk = json.loads(json_line)
                            yield chunk
                        except json.JSONDecodeError as e:
                            print(f"OllamaClient: Json decoding error for a stream line: '{json_line}' - {e}")
                            continue
                        except Exception as e:
                            print(f"OllamaClient: Error processing stream line: '{line}' - {e}")
                            continue

        except requests.exceptions.ConnectionError as e:
            print(f"OllamaClient: Connection error in generate_response - {e}")
            yield {'error': "Connection error", 'done': True}
        except requests.exceptions.Timeout as e:
            print(f"OllamaClient: Timeout error in generate_response - {e}")
            yield {'error': "Timeout error", 'done': True}
        except requests.exceptions.HTTPError as e:
            error_message = f"Http error {e.response.status_code} from Ollama server"
            try:
                ollama_error_detail = e.response.json().get('error', e.response.text)
                error_message += f": Details: {ollama_error_detail}"
            except json.JSONDecodeError:
                error_message += f": Details: {e.response.text}"
            print(f"OllamaClient: HTTP error in generate_response_stream - {error_message}")
            yield {'error': error_message, 'done': True}
        except Exception as e:
            print(f"OllamaClient: An unexpected error occurred in generate_response - {e}")
            yield {'error': f"Unexpected Error: {e}, 'done': True"}
