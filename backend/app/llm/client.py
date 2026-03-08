"""
LLM Client for CAD generation
"""

import json
import os
from typing import Optional, Dict, Any
from app.schema.models import CADModelPlan


class LLMClient:
    """Base class for LLM clients"""
    
    SYSTEM_PROMPT = """You are a professional CAD modeling engineer specializing in converting natural language descriptions into precise parametric CAD modeling plans.

Your task:
1. Understand the user's mechanical design requirements
2. Analyze geometric constraints and dimensional relationships
3. Plan reasonable modeling step sequences
4. Generate a strictly structured JSON modeling plan following the provided schema

Rules:
- ALL dimensions must be explicit, no ambiguity (words like "about", "around" are not allowed)
- Prioritize parametric design by defining key dimensions as parameters
- Modeling steps must follow geometric dependency order (create base first, then features)
- For complex designs, break down into multiple simple steps, never try to complete everything at once
- Use engineering-appropriate default values when requirements are unclear

Units: Default to millimeters (mm) unless user explicitly requests other units
Coordinate System: Default right-hand coordinate system, XY plane as base plane, Z-axis upward

Output Format: Must output valid JSON following the text-to-cad-schema-v1 format."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv(self._get_api_key_env())
    
    def _get_api_key_env(self) -> str:
        raise NotImplementedError
    
    async def generate_cad_plan(self, user_description: str) -> CADModelPlan:
        """Generate CAD plan from user description"""
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """Anthropic Claude client"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def _get_api_key_env(self) -> str:
        return "ANTHROPIC_API_KEY"
    
    async def generate_cad_plan(self, user_description: str) -> CADModelPlan:
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=self.api_key)
        
        user_prompt = f"""Generate a CAD modeling plan for the following mechanical design requirement:

Design Description:
{user_description}

Requirements:
1. Analyze the design requirements and identify all geometric features
2. Determine a reasonable modeling sequence
3. Generate a parametric JSON modeling plan
4. Ensure all dimensions are explicit and executable

Output only the JSON format modeling plan, no other explanatory text.
"""
        
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=self.SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract JSON from response
        content = response.content[0].text
        
        # Try to find JSON in the response
        try:
            # First try direct JSON parse
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                # Try to find JSON between curly braces
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    raise ValueError(f"Could not parse JSON from response: {content}")
        
        return CADModelPlan(**data)


class OpenAIClient(LLMClient):
    """OpenAI GPT client"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def _get_api_key_env(self) -> str:
        return "OPENAI_API_KEY"
    
    async def generate_cad_plan(self, user_description: str) -> CADModelPlan:
        client = self.client
        
        user_prompt = f"""Generate a CAD modeling plan for the following mechanical design requirement:

Design Description:
{user_description}

Output a valid JSON object following the CAD modeling plan schema."""
        
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=4096
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        return CADModelPlan(**data)


def get_llm_client(provider: str = "anthropic") -> LLMClient:
    """Factory function to get appropriate LLM client"""
    if provider == "anthropic":
        return AnthropicClient()
    elif provider == "openai":
        return OpenAIClient()
    else:
        raise ValueError(f"Unknown provider: {provider}")
