"""LiteLLM manager module for Ambrogio."""

from typing import Optional, Dict, Any, ClassVar
from litellm import completion


class LLMManager:
    """Singleton manager class for LiteLLM interactions."""

    _instance: ClassVar[Optional["LLMManager"]] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(
        cls, api_key: str, model: str = "gpt-4o-mini", api_base: Optional[str] = None
    ) -> "LLMManager":
        """Initialize the LLM manager singleton.

        Args:
            api_key: API key for the LLM provider
            model: Model identifier (default: gpt-3.5-turbo)
            api_base: Optional base URL for the API endpoint

        Returns:
            The singleton instance
        """
        instance = cls()
        if not instance._initialized:
            instance._init(api_key, model, api_base)
            instance._initialized = True
        return instance

    @classmethod
    def get_instance(cls) -> "LLMManager":
        """Get the singleton instance.

        Returns:
            The singleton instance

        Raises:
            RuntimeError: If the manager hasn't been initialized
        """
        if cls._instance is None or not cls._instance._initialized:
            raise RuntimeError(
                "LLMManager not initialized. Call LLMManager.initialize() first"
            )
        return cls._instance

    def _init(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        api_base: Optional[str] = None,
    ) -> None:
        """Internal initialization method.

        Args:
            api_key: API key for the LLM provider
            model: Model identifier (default: gpt-3.5-turbo)
            api_base: Optional base URL for the API endpoint
        """
        self.api_key = api_key
        self.model = model
        self.api_base = api_base

    def get_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Dict[str, Any],
    ) -> str:
        """Get completion from LiteLLM.

        Args:
            messages: List of message dictionaries, each with 'role' and 'content' keys
                     Example: [{"role": "system", "content": "You are a helpful assistant"},
                              {"role": "user", "content": "Hello"}]
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: None)
            **kwargs: Additional arguments to pass to litellm.completion

        Returns:
            Generated text response
        """
        # Remove messages from kwargs if present to avoid conflicts
        kwargs.pop("messages", None)

        response = completion(
            model=self.model,
            messages=messages,
            api_key=self.api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            api_base=self.api_base,
            **kwargs,
        )

        return response.choices[0].message.content
