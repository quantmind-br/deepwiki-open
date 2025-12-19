"""
Relationship extractor for inferring connections between code components.
"""

import json
import logging
from typing import List, Dict, Optional

from ..models import QueryIntent, EdgeType
from ..analyzer.base import AnalysisResult
from ..generator.edge_builder import LLMRelationship
from .prompts import PROMPTS
from api.config import get_model_config

logger = logging.getLogger(__name__)


class RelationshipExtractor:
    """
    Extracts relationships between code components using LLM.
    
    Augments static analysis with semantic understanding to find
    relationships that aren't obvious from code structure alone.
    """
    
    def __init__(self, provider: str = "google", model: Optional[str] = None):
        self.provider = provider
        self.model = model
    
    async def extract(
        self,
        query: str,
        analysis: Dict[str, AnalysisResult],
        query_intent: QueryIntent
    ) -> List[LLMRelationship]:
        """
        Extract relationships from code analysis results.
        
        Args:
            query: Original user query
            analysis: Dict of file_path -> AnalysisResult
            query_intent: Parsed query intent
            
        Returns:
            List of LLM-inferred relationships
        """
        try:
            # Build context for LLM
            analysis_summary = self._build_analysis_summary(analysis)
            symbols_list = self._build_symbols_list(analysis, query_intent)
            imports_list = self._build_imports_list(analysis)
            calls_list = self._build_calls_list(analysis)
            
            # Get model configuration
            config = get_model_config(self.provider, self.model)
            
            # Build prompts
            system_prompt = PROMPTS["relationship_extractor_system"]
            user_prompt = PROMPTS["relationship_extractor_user"].format(
                query=query,
                analysis_summary=analysis_summary,
                symbols_list=symbols_list,
                imports_list=imports_list,
                calls_list=calls_list
            )
            
            # Call LLM
            response_text = await self._call_llm(config, system_prompt, user_prompt)
            
            # Parse response
            relationships = self._parse_relationships(response_text)
            
            logger.info(f"Extracted {len(relationships)} relationships from LLM")
            return relationships
            
        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            return []
    
    def _build_analysis_summary(self, analysis: Dict[str, AnalysisResult]) -> str:
        """Build a summary of the analysis results"""
        total_files = len(analysis)
        total_symbols = sum(len(r.symbols) for r in analysis.values())
        total_imports = sum(len(r.imports) for r in analysis.values())
        total_calls = sum(len(r.calls) for r in analysis.values())
        
        languages = set(r.language for r in analysis.values())
        
        return f"""
Files analyzed: {total_files}
Total symbols found: {total_symbols}
Total imports: {total_imports}
Total function calls: {total_calls}
Languages: {', '.join(languages)}
"""
    
    def _build_symbols_list(
        self,
        analysis: Dict[str, AnalysisResult],
        query_intent: QueryIntent
    ) -> str:
        """Build a list of relevant symbols"""
        symbols = []
        
        for file_path, result in analysis.items():
            for symbol in result.symbols:
                # Check relevance to query
                relevance = self._calculate_relevance(symbol.name, query_intent)
                
                symbol_info = f"- {symbol.type.value}: {file_path}:{symbol.name}"
                if symbol.bases:
                    symbol_info += f" (extends: {', '.join(symbol.bases)})"
                if symbol.docstring:
                    # Truncate docstring
                    doc = symbol.docstring[:100].replace('\n', ' ')
                    symbol_info += f" - \"{doc}...\""
                
                symbols.append((relevance, symbol_info))
        
        # Sort by relevance and take top 50
        symbols.sort(key=lambda x: x[0], reverse=True)
        return "\n".join(s[1] for s in symbols[:50])
    
    def _build_imports_list(self, analysis: Dict[str, AnalysisResult]) -> str:
        """Build a list of imports"""
        imports = []
        
        for file_path, result in analysis.items():
            for imp in result.imports:
                if imp.resolved_path:
                    imports.append(f"- {file_path} imports {imp.resolved_path}")
                elif not imp.module.startswith('.'):
                    imports.append(f"- {file_path} imports external: {imp.module}")
        
        return "\n".join(imports[:30])  # Limit to 30
    
    def _build_calls_list(self, analysis: Dict[str, AnalysisResult]) -> str:
        """Build a list of function calls"""
        calls = []
        
        for file_path, result in analysis.items():
            for call in result.calls:
                calls.append(f"- {file_path}:{call.caller} -> {call.callee}")
        
        return "\n".join(calls[:40])  # Limit to 40
    
    def _calculate_relevance(self, name: str, query_intent: QueryIntent) -> float:
        """Calculate relevance of a symbol to the query"""
        score = 0.0
        name_lower = name.lower()
        
        for keyword in query_intent.keywords:
            if keyword.lower() in name_lower:
                score += 2.0
        
        for focus in query_intent.focus_areas:
            if focus.lower() in name_lower:
                score += 1.5
        
        return score
    
    async def _call_llm(self, config: dict, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM"""
        if self.provider == "google":
            from google import genai
            from api.config import GOOGLE_API_KEY
            
            client = genai.Client(api_key=GOOGLE_API_KEY)
            prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = client.models.generate_content(
                model=config["model_kwargs"].get("model", "gemini-2.0-flash"),
                contents=prompt
            )
            return response.text
            
        elif self.provider == "openai":
            import openai
            from api.config import OPENAI_API_KEY
            
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model=config["model_kwargs"].get("model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        else:
            # Fallback
            return "[]"
    
    def _parse_relationships(self, response: str) -> List[LLMRelationship]:
        """Parse relationships from LLM response"""
        relationships = []
        
        # Clean response
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            start = 1
            end = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end = i
                    break
            response = "\n".join(lines[start:end])
        
        try:
            data = json.loads(response)
            if not isinstance(data, list):
                data = [data]
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                # Map type string to EdgeType
                type_str = item.get("type", "uses").lower().replace("-", "_")
                edge_type = self._map_edge_type(type_str)
                
                relationships.append(LLMRelationship(
                    source=item.get("source", ""),
                    target=item.get("target", ""),
                    type=edge_type,
                    description=item.get("description", ""),
                    importance=item.get("importance", "medium")
                ))
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
        
        return relationships
    
    def _map_edge_type(self, type_str: str) -> EdgeType:
        """Map string to EdgeType enum"""
        type_map = {
            "calls": EdgeType.CALLS,
            "imports": EdgeType.IMPORTS,
            "extends": EdgeType.EXTENDS,
            "implements": EdgeType.IMPLEMENTS,
            "uses": EdgeType.USES,
            "data_flow": EdgeType.DATA_FLOW,
            "control_flow": EdgeType.CONTROL_FLOW,
            "depends_on": EdgeType.DEPENDS_ON,
            "returns": EdgeType.RETURNS,
            "instantiates": EdgeType.INSTANTIATES,
        }
        return type_map.get(type_str, EdgeType.USES)
