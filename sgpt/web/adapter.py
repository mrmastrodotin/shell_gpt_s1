from abc import ABC, abstractmethod
from typing import Any

class WebProviderAdapter(ABC):
    """
    Abstract base class for all web provider adapters.
    """
    
    @property
    @abstractmethod
    def url(self) -> str:
        """The URL of the provider."""
        pass

    @abstractmethod
    def preflight_check(self, page: Any) -> bool:
        """
        Check if the page is ready for automation.
        Should return True if ready, False otherwise.
        """
        pass

    @abstractmethod
    def send_prompt(self, page: Any, prompt: str) -> None:
        """
        Send the prompt to the provider.
        """
        pass

    @abstractmethod
    def extract_response(self, page: Any) -> str:
        """
        Extract the last response from the provider.
        This generic method can be overridden for specific logic.
        """
        pass
        
    @abstractmethod
    def wait_for_response(self, page: Any) -> None:
        """
        Wait for the response to be generated.
        """
        pass
