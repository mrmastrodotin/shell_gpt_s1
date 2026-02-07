"""
Async LLM Handler Wrapper
Wraps synchronous v1 LLM handlers for use in async agent loop
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any
import json


class AsyncLLMHandler:
    """Async wrapper for synchronous v1 LLM handlers"""
    
    def __init__(self, sync_handler, model: str = None, temperature: float = 0.7):
        """
        Initialize async wrapper
        
        Args:
            sync_handler: Synchronous v1 LLM handler
            model: Model name override
            temperature: Temperature setting
        """
        self.handler = sync_handler
        self.model = model
        self.temperature = temperature
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2000,
        response_format: str = "text"
    ) -> str:
        """
        Generate response asynchronously with retry logic
        
        Args:
            prompt: User prompt
            system: System prompt
            temperature: Temperature override
            max_tokens: Max tokens to generate
            response_format: "text" or "json"
            
        Returns:
            Generated response text or None on failure
        """
        from sgpt.agent.retry import RetryHandler
        
        loop = asyncio.get_event_loop()
        
        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Retry with exponential backoff
        async def _generate():
            return await loop.run_in_executor(
                self.executor,
                self._sync_generate,
                messages,
                temperature or self.temperature,
                max_tokens
            )
        
        response = await RetryHandler.retry_async(
            _generate,
            max_attempts=3,
            base_delay=2.0,
            exceptions=(Exception,)
        )
        
        # Fallback if all retries failed
        if response is None:
            print("⚠️  LLM generation failed after retries, using fallback")
            return self._get_fallback_response(prompt)
        
        return response
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Fallback response when LLM fails"""
        
        # Simple fallback based on prompt keywords
        if "json" in prompt.lower():
            # Return safe JSON fallback
            return '{"error": "LLM unavailable", "fallback": true}'
        
        return "LLM service temporarily unavailable. Please try again."
    
    def _sync_generate(self, messages: list, temperature: float, max_tokens: int) -> str:
        """Synchronous generation (runs in thread pool)"""
        
        # Convert messages to string for v1 handlers
        prompt_text = "\n\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in messages
        ])
        
        # Call sync handler
        # Note: v1 handlers have different interfaces
        # We need to adapt based on handler type
        
        try:
            # Try OpenAI-style handler
            if hasattr(self.handler, 'chat'):
                response = self.handler.chat(
                    messages=messages,
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response
            
            # Try simple generate
            elif hasattr(self.handler, 'generate'):
                response = self.handler.generate(
                    prompt_text,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response
            
            # Fallback
            else:
                return str(self.handler(prompt_text))
                
        except Exception as e:
            raise Exception(f"Handler generation failed: {e}")
    
    async def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        schema: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Generate JSON response
        
        Args:
            prompt: User prompt
            system: System prompt
            schema: Expected JSON schema
            
        Returns:
            Parsed JSON dict or None
        """
        # Add JSON instruction
        json_prompt = prompt + "\n\nRespond ONLY with valid JSON."
        
        response = await self.generate(
            prompt=json_prompt,
            system=system,
            temperature=0.3,  # Lower temp for structured output
            response_format="json"
        )
        
        if not response:
            return None
        
        # Try to parse JSON
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON: {e}")
            print(f"   Response: {response[:200]}")
            return None
    
    def __del__(self):
        """Cleanup thread pool"""
        self.executor.shutdown(wait=False)


def get_llm_handler(interface: str = "openai", model: str = None) -> AsyncLLMHandler:
    """
    Get async LLM handler for specified interface
    
    Args:
        interface: LLM interface (openai, gemini, ollama, web)
        model: Model name
        
    Returns:
        AsyncLLMHandler instance
    """
    # TODO: Import v1 handlers based on interface
    # For now, return mock handler for testing
    
    if interface == "openai":
        # from sgpt.llm.openai_handler import OpenAIHandler
        # sync_handler = OpenAIHandler(model=model or "gpt-4")
        print(f"🤖 LLM: OpenAI ({model or 'gpt-4'})")
        sync_handler = MockHandler()
        
    elif interface == "gemini":
        # from sgpt.llm.gemini_handler import GeminiHandler
        # sync_handler = GeminiHandler(model=model or "gemini-pro")
        print(f"🤖 LLM: Gemini ({model or 'gemini-pro'})")
        sync_handler = MockHandler()
        
    elif interface == "ollama":
        # from sgpt.llm.ollama_handler import OllamaHandler
        # sync_handler = OllamaHandler(model=model or "llama2")
        print(f"🤖 LLM: Ollama ({model or 'llama2'})")
        sync_handler = MockHandler()
        
    else:
        print(f"⚠️  Unknown interface: {interface}, using mock")
        sync_handler = MockHandler()
    
    return AsyncLLMHandler(sync_handler, model=model)


class MockHandler:
    """Mock LLM handler for testing"""
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Mock generation"""
        
        # Return simple JSON for testing
        if "Think" in prompt or "analyze" in prompt.lower():
            return json.dumps({
                "goal_satisfied": False,
                "should_transition": False,
                "reasoning": "Mock reasoning - Phase 3 testing"
            })
        
        elif "Plan" in prompt or "objective" in prompt.lower():
            return json.dumps({
                "objective": "Discover live hosts",
                "intent": "host_discovery"
            })
        
        elif "Propose" in prompt or "tool" in prompt.lower():
            return json.dumps({
                "tool": "nmap",
                "action": "host_discovery",
                "parameters": {"subnet": "192.168.1.0/24"}
            })
        
        elif "Summarize" in prompt or "extract" in prompt.lower():
            return json.dumps({
                "hosts": ["192.168.1.1", "192.168.1.10"],
                "confidence": "high"
            })
        
        else:
            return "Mock LLM response"
