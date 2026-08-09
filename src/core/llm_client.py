"""
LLM Client for ThinkingModels

This module provides a client for interacting with LLM APIs
with proper error handling, retry logic, and configuration support.
"""

import os
import time
import json
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """
    Configuration for LLM API client
    """
    api_url: str
    api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """
        Create config from environment variables

        Returns:
            LLMConfig instance with values from environment
        """
        api_url = os.getenv('LLM_API_URL')
        if not api_url:
            raise ValueError("LLM_API_URL environment variable must be set")

        return cls(
            api_url=api_url,
            api_key=os.getenv('LLM_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            model_name=os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo'),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.7')),
            max_tokens=int(os.getenv('LLM_MAX_TOKENS', '2000')),
            timeout=int(os.getenv('LLM_TIMEOUT', '30')),
            max_retries=int(os.getenv('LLM_MAX_RETRIES', '3')),
            retry_delay=float(os.getenv('LLM_RETRY_DELAY', '1.0'))
        )

class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.
    """
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the LLM.
        """
        pass

    @abstractmethod
    def request_model_selection(self, query: str, available_models: List[Dict[str, Any]]) -> List[str]:
        """
        Request LLM to select relevant thinking models for a query.
        """
        pass

    @abstractmethod
    def request_solution(self, query: str, selected_models: List[Dict[str, Any]]) -> str:
        """
        Request LLM to solve a problem using selected thinking models.
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the LLM API.
        """
        pass


class OpenAIClient(BaseLLMClient):
    """
    Client for interacting with OpenAI-compatible LLM APIs.
    """
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the OpenAI client.
        """
        super().__init__(config or LLMConfig.from_env())
        self.session = requests.Session()

        # Set up headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ThinkingModels/1.0'
        })

        # Add API key if provided
        if self.config.api_key:
            self.session.headers['Authorization'] = f'Bearer {self.config.api_key}'

    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Make a request to the LLM API with retry logic.
        """
        payload = {
            'model': self.config.model_name,
            'messages': messages,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            **kwargs
        }

        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Making OpenAI API request (attempt {attempt + 1}/{self.config.max_retries})")

                # Determine the correct endpoint
                if self.config.api_url.endswith('/v1') or self.config.api_url.endswith('/v1/'):
                    endpoint = f"{self.config.api_url.rstrip('/')}/chat/completions"
                else:
                    endpoint = f"{self.config.api_url.rstrip('/')}/v1/chat/completions"

                response = self.session.post(
                    endpoint,
                    json=payload,
                    timeout=self.config.timeout
                )

                response.raise_for_status()
                result = response.json()

                logger.info("OpenAI API request successful")
                return result

            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"API request failed (attempt {attempt + 1}): {str(e)}")

                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))

        raise RuntimeError(f"OpenAI API request failed after {self.config.max_retries} attempts. Last error: {last_error}")

    def _extract_content(self, response: Dict[str, Any]) -> str:
        """
        Extract content from OpenAI API response.
        """
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid API response format: {e}")

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._make_request(messages)
        return self._extract_content(response)

    def request_model_selection(self, query: str, available_models: List[Dict[str, Any]]) -> List[str]:
        system_prompt = """
You are an expert at selecting relevant thinking models for problem-solving.
Given a user query and a list of available thinking models with their definitions, select only those that are potentially helpful.

Your response should be a JSON list of model IDs, like: ["model1", "model2", "model3"]
Select between 0-3 of the most relevant models. Only select a model when it's truly useful. If no model fits, select none.
"""

        models_text = ""
        for model in available_models:
            models_text += f"**{model['id']}**: {model['definition'][:300]}...\n\n"

        user_prompt = f"""
User Query: {query}

Available Thinking Models:
{models_text}

Select the most relevant thinking models for this query:
"""

        response = self.generate_response(user_prompt, system_prompt)

        try:
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:-3].strip()
            elif response.startswith('```'):
                response = response[3:-3].strip()

            selected_models = json.loads(response)

            available_model_ids = [model['id'] for model in available_models]
            valid_models = [model for model in selected_models if model in available_model_ids]

            valid_models = valid_models[:3]

            if not valid_models:
                logger.warning("No valid models selected, returning empty list")
                return []

            return valid_models

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse model selection response: {response}")
            return []

    def request_solution(self, query: str, selected_models: List[Dict[str, Any]]) -> str:
        system_prompt = """
You are an expert problem solver. You have been provided with thinking models that may assist in solving a user's query.
Only use these thinking models as guidance if they are helpful. Otherwise, feel free to ignore them.

For each thinking model provided, consider:
1. Its applicability to the problem
2. Whether using its methodology adds value
3. If so, explicitly reference it in your solution

Provide a clear, structured response that demonstrates thoughtful application when relevant, but don't force their use.
"""

        models_text = ""
        for i, model in enumerate(selected_models, 1):
            models_text += f"""
{i}. **{model['id']}** ({model['type']})
   Definition: {model['definition']}

   Examples:
"""
            for j, example in enumerate(model['examples'], 1):
                models_text += f"   {j}. {example[:200]}...\n"
            models_text += "\n"

        user_prompt = f"""
User Query: {query}

Relevant Thinking Models:
{models_text}

Using these thinking models as guidance, provide a comprehensive solution to the user's query:
"""

        return self.generate_response(user_prompt, system_prompt)

    def test_connection(self) -> bool:
        try:
            response = self.generate_response("Hello, please respond with 'OK' if you can hear me.")
            return "OK" in response or "ok" in response.lower()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

import google.generativeai as genai

class GeminiClient(BaseLLMClient):
    """
    Client for interacting with Google Gemini LLM API.
    """
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the Gemini client.
        """
        super().__init__(config or LLMConfig.from_env())
        if not self.config.gemini_api_key:
            raise ValueError("GEMINI_API_KEY must be set for GeminiClient")
        genai.configure(api_key=self.config.gemini_api_key)
        self.model = genai.GenerativeModel(self.config.model_name)

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the Gemini LLM.
        Note: Gemini API has a different way of handling system prompts.
        It's usually part of the initial conversation history.
        """
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        try:
            logger.info(f"Making Gemini API request with model {self.config.model_name}")
            response = self.model.generate_content(full_prompt)
            logger.info("Gemini API request successful")
            return response.text
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            raise RuntimeError(f"Gemini API request failed: {e}")

    def request_model_selection(self, query: str, available_models: List[Dict[str, Any]]) -> List[str]:
        # This implementation can be largely the same as OpenAI's,
        # as the logic for prompt creation is abstract enough.
        system_prompt = """
You are an expert at selecting relevant thinking models for problem-solving.
Given a user query and a list of available thinking models with their definitions, select only those that are potentially helpful.

Your response should be a JSON list of model IDs, like: ["model1", "model2", "model3"]
Select between 0-3 of the most relevant models. Only select a model when it's truly useful. If no model fits, select none.
"""
        models_text = ""
        for model in available_models:
            models_text += f"**{model['id']}**: {model['definition'][:300]}...\n\n"

        user_prompt = f"""
User Query: {query}

Available Thinking Models:
{models_text}

Select the most relevant thinking models for this query:
"""
        response_text = self.generate_response(user_prompt, system_prompt)

        try:
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()

            selected_models = json.loads(response_text)

            available_model_ids = [m['id'] for m in available_models]
            valid_models = [m for m in selected_models if m in available_model_ids][:3]

            if not valid_models:
                logger.warning("No valid models selected by Gemini, returning empty list")
            return valid_models
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse model selection response from Gemini: {response_text}")
            return []

    def request_solution(self, query: str, selected_models: List[Dict[str, Any]]) -> str:
        system_prompt = """
You are an expert problem solver. You have been provided with thinking models that may assist in solving a user's query.
Only use these thinking models as guidance if they are helpful. Otherwise, feel free to ignore them.
Provide a clear, structured response.
"""
        models_text = ""
        for i, model in enumerate(selected_models, 1):
            models_text += f"\n{i}. **{model['id']}** ({model['type']}): {model['definition']}"

        user_prompt = f"""
User Query: {query}

Relevant Thinking Models:
{models_text}

Using these thinking models as guidance, provide a comprehensive solution to the user's query:
"""
        return self.generate_response(user_prompt, system_prompt)

    def test_connection(self) -> bool:
        try:
            response = self.generate_response("Hello, please respond with 'OK' if you can hear me.")
            return "OK" in response or "ok" in response.lower()
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False

from config import get_config

def get_llm_client() -> BaseLLMClient:
    """
    Factory function to get the appropriate LLM client based on configuration.
    """
    config = get_config()

    if config.llm_provider.lower() == 'gemini':
        # For Gemini, the API key is passed differently
        gemini_config = LLMConfig(
            api_url="", # Not used by Gemini SDK
            gemini_api_key=config.gemini_api_key, # Correctly assign to gemini_api_key
            api_key=None, # Explicitly set OpenAI key to None
            model_name=config.llm_model_name,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens
        )
        return GeminiClient(config=gemini_config)


    # Default to OpenAI
    openai_config = LLMConfig(
        api_url=config.llm_api_url,
        api_key=config.llm_api_key,
        gemini_api_key=None,  # Explicitly null for OpenAI
        model_name=config.llm_model_name,
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
        timeout=config.llm_timeout,
        max_retries=config.llm_max_retries,
        retry_delay=config.llm_retry_delay
    )
    return OpenAIClient(config=openai_config)


