# ollama_client.py
import requests
import json
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with the Ollama API.
    Handles communication with a local or remote Ollama server.
    """

    def __init__(self, base_url="http://localhost:11434"):
        """
        Initialize the Ollama client.

        Args:
            base_url (str): Base URL of the Ollama server.
        """
        self.base_url = base_url
        logger.debug(f"OllamaClient initialized with base_url: {base_url}")

    def get_models(self):
        """
        Fetches the list of available models from the Ollama Server.

        Returns:
            List[str]: List of model names

        Raises:
            ConnectionError: If unable to connect to the Ollama server
            ValueError: If there's an issue with the URL or response format
            TimeoutError: If the request times out
            Exception: For other unexpected errors
        """
        try:
            if not (self.base_url.startswith("http://") or self.base_url.startswith("https://")):
                raise requests.exceptions.MissingSchema(f"URL scheme (http/https) is missing from base_url: {self.base_url}")
            url = f"{self.base_url.rstrip('/')}/api/tags"

            logger.debug(f"Fetching models from {url}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            models = data.get('models', [])
            model_names = [model['name'] for model in models]
            logger.debug(f"Fetched {len(model_names)} models from Ollama")
            return model_names
        except requests.exceptions.MissingSchema as e:
            logger.error(f"Critical URL error in get_models - {e}")
            raise ValueError(f"Invalid URL to get_models: {e}. Ensure URL includes 'http://' or 'https://'.") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error in get_models - {e}")
            raise ConnectionError("Failed to connect to Ollama server while fetching models.") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error in get_models - {e}")
            raise TimeoutError("Request to Ollama timed out while fetching models.") from e
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error in get_models - {e.response.status_code} - {e.response.text}")
            raise ValueError(f"HTTP error {e.response.status_code} from Ollama server while fetching models") from e
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error in get_models - {e}")
            raise ValueError("Failed to decode JSON response while fetching models.") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred in get_models - {e}")
            raise Exception("An unexpected error occurred while fetching models.") from e

    def generate_response_stream(self, model_name, prompt, context=None):
        """
        Generate a response from the Ollama server using the specified model, yielding parts of the response.

        Args:
            model_name (str): The name of the model to use for generation.
            prompt (str): The input prompt for the model.
            context (List[int], optional): Previous conversation context. Defaults to None.

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
            if context:  # Ollama docs say context will be deprecated, find out why and other solution?
                payload['context'] = context

            logger.debug(f"Sending payload to {url}")

            with requests.post(url, json=payload, stream=True, timeout=300) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        try:
                            json_line = line.decode('utf-8')
                            chunk = json.loads(json_line)
                            yield chunk
                        except json.JSONDecodeError as e:
                            logger.error(f"Json decoding error for a stream line: '{json_line}' - {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing stream line: '{line}' - {e}")
                            continue

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error in generate_response - {e}")
            yield {'error': "Connection error", 'done': True}
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error in generate_response - {e}")
            yield {'error': "Timeout error", 'done': True}
        except requests.exceptions.HTTPError as e:
            error_message = f"Http error {e.response.status_code} from Ollama server"
            try:
                ollama_error_detail = e.response.json().get('error', e.response.text)
                error_message += f": Details: {ollama_error_detail}"
            except json.JSONDecodeError:
                error_message += f": Details: {e.response.text}"
            logger.error(f"HTTP error in generate_response_stream - {error_message}")
            yield {'error': error_message, 'done': True}
        except Exception as e:
            logger.error(f"An unexpected error occurred in generate_response - {e}")
            yield {'error': f"Unexpected Error: {e}", 'done': True}
