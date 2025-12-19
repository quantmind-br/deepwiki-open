"""
Trace guide writer for generating explanatory documentation.
"""

import json
import logging
from typing import Dict, Optional

from ..models import TraceGuide, TraceSection, CodemapGraph, QueryIntent, Importance
from ..analyzer.base import AnalysisResult
from .prompts import PROMPTS
from api.config import get_model_config

logger = logging.getLogger(__name__)


class TraceWriter:
    """
    Generates trace guides that explain code flows in plain language.
    
    Uses LLM to create structured, readable documentation from
    the codemap graph.
    """
    
    def __init__(self, provider: str = "google", model: Optional[str] = None):
        self.provider = provider
        self.model = model
    
    async def write(
        self,
        query: str,
        language: str,
        graph: CodemapGraph,
        analysis: Dict[str, AnalysisResult],
        query_intent: QueryIntent
    ) -> TraceGuide:
        """
        Generate a trace guide for a codemap.
        
        Args:
            query: Original user query
            language: Output language (e.g., "en", "es")
            graph: The generated codemap graph
            analysis: Code analysis results
            query_intent: Parsed query intent
            
        Returns:
            TraceGuide object
        """
        try:
            # Build context for LLM
            nodes_summary = self._build_nodes_summary(graph)
            edges_summary = self._build_edges_summary(graph)
            clusters_summary = self._build_clusters_summary(graph)
            
            # Get model configuration
            config = get_model_config(self.provider, self.model)
            
            # Build prompts
            system_prompt = PROMPTS["trace_guide_system"]
            user_prompt = PROMPTS["trace_guide_user"].format(
                query=query,
                language=language,
                node_count=len(graph.nodes),
                edge_count=len(graph.edges),
                root_nodes=", ".join(graph.root_nodes[:5]),
                nodes_summary=nodes_summary,
                edges_summary=edges_summary,
                clusters_summary=clusters_summary
            )
            
            # Add language instruction
            if language != "en":
                system_prompt += f"\n\nIMPORTANT: Write all content in {self._get_language_name(language)}."
            
            # Call LLM
            response_text = await self._call_llm(config, system_prompt, user_prompt)
            
            # Parse response
            trace_guide = self._parse_trace_guide(response_text, graph)
            
            return trace_guide
            
        except Exception as e:
            logger.error(f"Error writing trace guide: {e}")
            return self._fallback_trace_guide(query, graph)
    
    def _build_nodes_summary(self, graph: CodemapGraph) -> str:
        """Build a summary of important nodes"""
        # Sort by importance
        sorted_nodes = sorted(
            graph.nodes,
            key=lambda n: {
                Importance.CRITICAL: 4,
                Importance.HIGH: 3,
                Importance.MEDIUM: 2,
                Importance.LOW: 1
            }.get(n.importance, 0),
            reverse=True
        )
        
        lines = []
        for node in sorted_nodes[:20]:
            location_info = ""
            if node.location:
                location_info = f" ({node.location.file_path}:{node.location.line_start})"
            
            lines.append(
                f"- [{node.importance.value}] {node.type.value}: {node.label}{location_info}"
            )
            if node.description:
                lines.append(f"  Description: {node.description[:100]}")
        
        return "\n".join(lines)
    
    def _build_edges_summary(self, graph: CodemapGraph) -> str:
        """Build a summary of edges"""
        lines = []
        
        # Group edges by type
        edges_by_type = {}
        for edge in graph.edges:
            edges_by_type.setdefault(edge.type.value, []).append(edge)
        
        for edge_type, edges in edges_by_type.items():
            lines.append(f"\n{edge_type.upper()} relationships ({len(edges)} total):")
            for edge in edges[:10]:  # Show first 10 of each type
                label = f" ({edge.label})" if edge.label else ""
                lines.append(f"  - {edge.source} -> {edge.target}{label}")
        
        return "\n".join(lines)
    
    def _build_clusters_summary(self, graph: CodemapGraph) -> str:
        """Build a summary of clusters"""
        if not graph.clusters:
            return "No clusters defined"
        
        lines = []
        for cluster_name, node_ids in graph.clusters.items():
            lines.append(f"- {cluster_name}: {len(node_ids)} nodes")
        
        return "\n".join(lines)
    
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
                temperature=0.5
            )
            return response.choices[0].message.content
        else:
            return "{}"
    
    def _parse_trace_guide(self, response: str, graph: CodemapGraph) -> TraceGuide:
        """Parse trace guide from LLM response"""
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
            
            sections = []
            for i, section_data in enumerate(data.get("sections", [])):
                sections.append(TraceSection(
                    id=section_data.get("id", f"section-{i+1}"),
                    title=section_data.get("title", f"Section {i+1}"),
                    content=section_data.get("content", ""),
                    node_ids=section_data.get("node_ids", []),
                    order=section_data.get("order", i)
                ))
            
            return TraceGuide(
                title=data.get("title", "Code Trace Guide"),
                summary=data.get("summary", "Analysis of the requested code flow."),
                sections=sections,
                conclusion=data.get("conclusion")
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse trace guide JSON: {e}")
            return self._fallback_trace_guide("", graph)
    
    def _fallback_trace_guide(self, query: str, graph: CodemapGraph) -> TraceGuide:
        """Generate a basic trace guide when LLM fails"""
        sections = []
        
        # Create sections based on node types
        node_types = {}
        for node in graph.nodes:
            node_types.setdefault(node.type.value, []).append(node)
        
        order = 0
        for node_type, nodes in node_types.items():
            if not nodes:
                continue
            
            content_lines = []
            for node in nodes[:10]:
                content_lines.append(f"- **{node.label}**: {node.description or 'No description'}")
            
            sections.append(TraceSection(
                id=f"section-{node_type}",
                title=f"{node_type.replace('_', ' ').title()}s",
                content="\n".join(content_lines),
                node_ids=[n.id for n in nodes],
                order=order
            ))
            order += 1
        
        return TraceGuide(
            title=f"Code Map: {query[:50]}..." if len(query) > 50 else f"Code Map: {query}",
            summary=f"This code map shows {len(graph.nodes)} components and {len(graph.edges)} relationships.",
            sections=sections,
            conclusion="Explore the graph to understand how these components interact."
        )
    
    def _get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "pt": "Portuguese",
            "pt-br": "Brazilian Portuguese",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ru": "Russian",
            "it": "Italian",
        }
        return languages.get(code, "English")
