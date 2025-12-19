"""
Query parser for understanding user intent from natural language.
"""

import json
import logging
from typing import Optional

from ..models import QueryIntent
from .prompts import PROMPTS
from api.config import get_model_config

logger = logging.getLogger(__name__)


class QueryParser:
    """
    Parses natural language queries to extract intent and parameters.
    
    Uses LLM to understand what the user wants to explore in the codebase.
    """
    
    def __init__(self, provider: str = "google", model: Optional[str] = None):
        self.provider = provider
        self.model = model
    
    async def parse(
        self,
        query: str,
        language: str = "unknown",
        main_files: str = ""
    ) -> QueryIntent:
        """
        Parse a user query to extract intent.
        
        Args:
            query: Natural language query
            language: Primary programming language of the repo
            main_files: Comma-separated list of main files
            
        Returns:
            QueryIntent object
        """
        try:
            # Get model configuration
            config = get_model_config(self.provider, self.model)
            
            # Build messages for the LLM
            system_prompt = PROMPTS["query_parser_system"]
            user_prompt = PROMPTS["query_parser_user"].format(
                query=query,
                language=language,
                main_files=main_files or "Not specified"
            )
            
            # Call the LLM
            response_text = await self._call_llm(config, system_prompt, user_prompt)
            
            # Parse JSON response
            intent_data = self._parse_json_response(response_text)
            
            return QueryIntent(
                intent=intent_data.get("intent", "understand_flow"),
                focus_areas=intent_data.get("focus_areas", []),
                analysis_type=intent_data.get("analysis_type", "general"),
                preferred_layout=intent_data.get("preferred_layout", "hierarchical"),
                depth=min(max(intent_data.get("depth", 3), 1), 5),
                keywords=intent_data.get("keywords", self._extract_keywords(query))
            )
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            # Return a default intent based on simple keyword matching
            return self._fallback_parse(query)
    
    async def _call_llm(self, config: dict, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM with the given prompts"""
        model_client = config["model_client"]()
        model_kwargs = config["model_kwargs"].copy()
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call based on provider
        if self.provider == "google":
            return await self._call_google(model_client, model_kwargs, messages)
        elif self.provider == "openai":
            return await self._call_openai(model_client, model_kwargs, messages)
        else:
            return await self._call_generic(model_client, model_kwargs, messages)
    
    async def _call_google(self, client, kwargs: dict, messages: list) -> str:
        """Call Google Gemini API"""
        from google import genai
        from api.config import GOOGLE_API_KEY
        
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # Combine system and user messages for Gemini
        prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
        
        response = client.models.generate_content(
            model=kwargs.get("model", "gemini-2.0-flash"),
            contents=prompt
        )
        
        return response.text
    
    async def _call_openai(self, client, kwargs: dict, messages: list) -> str:
        """Call OpenAI API"""
        import openai
        from api.config import OPENAI_API_KEY
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=kwargs.get("model", "gpt-4o-mini"),
            messages=messages,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    async def _call_generic(self, client, kwargs: dict, messages: list) -> str:
        """Generic LLM call using adalflow"""
        import adalflow as adal
        
        generator = adal.Generator(
            model_client=client,
            model_kwargs=kwargs
        )
        
        prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
        response = generator(prompt_kwargs={"input": prompt})
        
        return response.data if hasattr(response, 'data') else str(response)
    
    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response"""
        # Try to extract JSON from the response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            # Find the JSON content between code blocks
            start = 1 if lines[0].startswith("```") else 0
            end = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end = i
                    break
            response = "\n".join(lines[start:end])
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return {}
    
    def _extract_keywords(self, query: str) -> list:
        """Extract keywords from query using simple heuristics"""
        # Remove common words
        stop_words = {
            'how', 'does', 'the', 'what', 'is', 'are', 'show', 'me', 'find',
            'where', 'when', 'why', 'can', 'you', 'explain', 'trace', 'flow',
            'work', 'works', 'working', 'a', 'an', 'in', 'to', 'for', 'of',
            'and', 'or', 'this', 'that', 'these', 'those', 'i', 'want'
        }
        
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _fallback_parse(self, query: str) -> QueryIntent:
        """Fallback parsing using simple keyword matching"""
        query_lower = query.lower()
        
        # Determine intent
        if any(w in query_lower for w in ['flow', 'trace', 'path', 'execution']):
            intent = "understand_flow"
            analysis_type = "control_flow"
        elif any(w in query_lower for w in ['depend', 'import', 'require', 'use']):
            intent = "find_dependencies"
            analysis_type = "dependencies"
        elif any(w in query_lower for w in ['data', 'variable', 'state', 'pass']):
            intent = "trace_data"
            analysis_type = "data_flow"
        elif any(w in query_lower for w in ['architecture', 'structure', 'overview', 'design']):
            intent = "architecture_overview"
            analysis_type = "architecture"
        elif any(w in query_lower for w in ['call', 'invoke', 'function', 'method']):
            intent = "understand_flow"
            analysis_type = "call_graph"
        else:
            intent = "explain_feature"
            analysis_type = "general"
        
        # Determine layout
        if analysis_type in ("architecture", "dependencies"):
            layout = "hierarchical"
        elif analysis_type in ("call_graph", "control_flow"):
            layout = "force"
        else:
            layout = "hierarchical"
        
        return QueryIntent(
            intent=intent,
            focus_areas=[],
            analysis_type=analysis_type,
            preferred_layout=layout,
            depth=3,
            keywords=self._extract_keywords(query)
        )
