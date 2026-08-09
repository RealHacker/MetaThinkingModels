"""
Configuration management for ThinkingModels project
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """
    Main configuration class for ThinkingModels
    """
    # Model Parser Settings
    models_directory: str = "models"
    
    # LLM API Settings
    llm_api_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    llm_provider: str = "openai"
    llm_model_name: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout: int = 30
    llm_max_retries: int = 3
    llm_retry_delay: float = 1.0
    
    # CLI Settings
    cli_interactive: bool = True
    cli_output_format: str = "text"  # text, json, markdown
    
    # Web Server Settings
    web_host: str = "127.0.0.1"
    web_port: int = 8000
    web_debug: bool = False
    
    # Logging Settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        Create configuration from environment variables
        
        Returns:
            Config instance with values from environment
        """
        return cls(
            # Model Parser Settings
            models_directory=os.getenv('THINKING_MODELS_DIR', 'models'),
            
            # LLM API Settings
            llm_api_url=os.getenv('LLM_API_URL'),
            llm_api_key=os.getenv('LLM_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            llm_provider=os.getenv('LLM_PROVIDER', 'openai'),
            llm_model_name=os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo'),
            llm_temperature=float(os.getenv('LLM_TEMPERATURE', '0.7')),
            llm_max_tokens=int(os.getenv('LLM_MAX_TOKENS', '2000')),
            llm_timeout=int(os.getenv('LLM_TIMEOUT', '30')),
            llm_max_retries=int(os.getenv('LLM_MAX_RETRIES', '3')),
            llm_retry_delay=float(os.getenv('LLM_RETRY_DELAY', '1.0')),
            
            # CLI Settings
            cli_interactive=os.getenv('CLI_INTERACTIVE', 'true').lower() == 'true',
            cli_output_format=os.getenv('CLI_OUTPUT_FORMAT', 'text'),
            
            # Web Server Settings
            web_host=os.getenv('WEB_HOST', '127.0.0.1'),
            web_port=int(os.getenv('WEB_PORT', '8000')),
            web_debug=os.getenv('WEB_DEBUG', 'false').lower() == 'true',
            
            # Logging Settings
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE')
        )
    
    def validate(self) -> None:
        """
        Validate configuration settings
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.llm_api_url:
            raise ValueError("LLM_API_URL must be set")
        
        if self.llm_temperature < 0 or self.llm_temperature > 2:
            raise ValueError("LLM temperature must be between 0 and 2")
        
        if self.llm_max_tokens < 1:
            raise ValueError("LLM max_tokens must be positive")
        
        if self.cli_output_format not in ['text', 'json', 'markdown']:
            raise ValueError("CLI output format must be 'text', 'json', or 'markdown'")
        
        if self.web_port < 1 or self.web_port > 65535:
            raise ValueError("Web port must be between 1 and 65535")
        
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError("Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")


# Global configuration instance
config = Config.from_env()


def get_config() -> Config:
    """
    Get the global configuration instance
    
    Returns:
        Config instance
    """
    return config


def update_config(**kwargs) -> None:
    """
    Update configuration settings
    
    Args:
        **kwargs: Configuration settings to update
    """
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")


def validate_config() -> None:
    """
    Validate the current configuration
    
    Raises:
        ValueError: If configuration is invalid
    """
    config.validate()
