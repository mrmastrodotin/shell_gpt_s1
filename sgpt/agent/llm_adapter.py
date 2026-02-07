"""
LLM Adapter for Agent
Integrates v1 interface system with v2 agent
"""

from typing import Optional, Any
from sgpt.config import cfg
from sgpt.llm.handler import get_llm_handler
import json


class AgentLLMAdapter:
    """
    Adapter to use v1 LLM interfaces with v2 agent
    
    Supports all v1 interfaces:
    - OpenAI
    - Gemini
    - Ollama
    - Web automation
    """
    
    def __init__(
        self,
        interface: str = None,
        model: str = None,
        temperature: float = None
    ):
        """
        Initialize LLM adapter
        
        Args:
            interface: LLM interface (openai, gemini, ollama, web)
            model: Model name (uses default if not specified)
            temperature: Temperature (uses default if not specified)
        """
        self.interface = interface or cfg.get("DEFAULT_INTERFACE", "openai")
        self.model = model or cfg.get("DEFAULT_MODEL")
        self.temperature = temperature or float(cfg.get("DEFAULT_TEMPERATURE", 0.1))
        
        # Get v1 handler
        self.handler = get_llm_handler(
            interface=self.interface,
            model=self.model
        )
    
    async def call(
        self,
        prompt: str,
        system_prompt: str = None,
        output_schema: dict = None,
        max_tokens: int = 2000
    ) -> dict:
        """
        Call LLM with prompt
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            output_schema: JSON schema for structured output
            max_tokens: Max tokens to generate
        
        Returns:
            Parsed JSON response (if schema provided) or raw text
        """
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Add JSON schema instruction if provided
        if output_schema:
            schema_instruction = f"\n\nRespond with ONLY valid JSON matching this schema:\n{json.dumps(output_schema, indent=2)}"
            messages[-1]["content"] += schema_instruction
        
        # Call handler
        try:
            response = await self.handler.generate(
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            
            # Parse JSON if schema provided
            if output_schema:
                # Extract JSON from response
                response_text = response.strip()
                
                # Handle markdown code blocks
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()
                
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError as e:
                    # Fallback: try to extract JSON from text
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
                    raise ValueError(f"Failed to parse JSON: {e}\nResponse: {response_text}")
            
            return {"text": response}
            
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count"""
        # Simple estimation: ~4 chars per token
        return len(text) // 4
    
    @property
    def supports_json(self) -> bool:
        """Check if interface supports JSON mode"""
        # OpenAI and Gemini have good JSON support
        return self.interface in ["openai", "gemini"]
    
    @property
    def is_local(self) -> bool:
        """Check if using local model"""
        return self.interface == "ollama"
