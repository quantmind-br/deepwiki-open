"""
Main orchestrator for codemap generation.
"""

import asyncio
import logging
import subprocess
import hashlib
from typing import Optional, Callable, Dict
from datetime import datetime
from functools import lru_cache
import uuid
import os

from .models import (
    Codemap, CodemapGraph, CodemapGenerateRequest, CodemapRenderOutput,
    CodemapProgress, CodemapStatus, QueryIntent
)
from .analyzer import get_analyzer
from .analyzer.base import AnalysisResult
from .generator import NodeBuilder, EdgeBuilder, Clusterer, Pruner, LayoutEngine
from .renderer import MermaidRenderer, JSONRenderer
from .llm import QueryParser, RelationshipExtractor, TraceWriter
from .storage import CodemapStorage
from .cache import AnalysisCache, get_content_hash

from api.rag import RAG

logger = logging.getLogger(__name__)

# LRU cache for query intents (caches last 500 queries)
@lru_cache(maxsize=500)
def _cached_query_hash(query_hash: str) -> None:
    """Placeholder for cached query intents - actual caching done via dict"""
    pass

# Global cache for query intents
_query_intent_cache: Dict[str, QueryIntent] = {}


class CodemapEngine:
    """
    Main orchestrator for codemap generation.
    
    Pipeline:
    1. Parse query to understand intent
    2. Retrieve relevant code via RAG
    3. Analyze code structure (AST, imports, calls)
    4. Build graph (nodes, edges)
    5. Prune and cluster
    6. Generate layout
    7. Render outputs (Mermaid, JSON)
    8. Generate trace guide
    """
    
    def __init__(
        self,
        provider: str = "google",
        model: Optional[str] = None
    ):
        self.provider = provider
        self.model = model
        
        # Initialize LLM components
        self.query_parser = QueryParser(provider, model)
        self.relationship_extractor = RelationshipExtractor(provider, model)
        self.trace_writer = TraceWriter(provider, model)
        
        # Initialize graph components
        self.node_builder = NodeBuilder()
        self.edge_builder = EdgeBuilder()
        self.clusterer = Clusterer()
        self.pruner = Pruner()
        self.layout_engine = LayoutEngine()
        
        # Initialize renderers
        self.mermaid_renderer = MermaidRenderer()
        self.json_renderer = JSONRenderer()
        
        # Initialize storage and cache
        self.storage = CodemapStorage()
        self.analysis_cache = AnalysisCache()
    
    async def generate(
        self,
        request: CodemapGenerateRequest,
        progress_callback: Optional[Callable[[CodemapProgress], None]] = None
    ) -> Codemap:
        """
        Generate a complete codemap from a user query.
        
        Args:
            request: Generation request with query and options
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete Codemap object
        """
        codemap_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Parse query (with caching)
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.ANALYZING,
                progress_percent=5,
                current_step="Parsing query...",
            ))
            
            # Check query intent cache
            query_hash = hashlib.md5(request.query.encode()).hexdigest()
            query_intent = _query_intent_cache.get(query_hash)
            if query_intent is None:
                query_intent = await self.query_parser.parse(request.query)
                _query_intent_cache[query_hash] = query_intent
                logger.debug(f"Query intent cached for hash {query_hash[:8]}")
            else:
                logger.debug(f"Query intent cache hit for hash {query_hash[:8]}")
            
            analysis_type = request.analysis_type if request.analysis_type != "auto" else query_intent.analysis_type
            
            # Step 2: Load repository and RAG
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.ANALYZING,
                progress_percent=10,
                current_step="Loading repository...",
            ))
            
            repo_info = self._parse_repo_url(request.repo_url)
            rag = RAG(provider=self.provider, model=self.model)
            rag.prepare_retriever(
                repo_url_or_path=request.repo_url,
                type=request.type or "github",
                access_token=request.token,
                excluded_dirs=request.excluded_dirs,
                excluded_files=request.excluded_files,
                included_dirs=request.included_dirs,
                included_files=request.included_files
            )
            
            repo_path = rag.db_manager.repo_paths["save_repo_dir"]
            commit_hash = self._get_repo_head_hash(repo_path)
            
            # Detect primary language
            primary_language = self._detect_language(repo_path, rag.transformed_docs)
            
            # Step 3: Retrieve relevant documents via RAG
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.ANALYZING,
                progress_percent=20,
                current_step="Finding relevant code...",
            ))
            
            retrieval = rag.retriever(
                request.query,
                top_k=min(request.max_nodes * 2, 100)
            )
            
            # The retriever returns raw results with doc_indices, need to populate documents
            retrieval_result = retrieval[0] if isinstance(retrieval, list) else retrieval
            if hasattr(retrieval_result, 'doc_indices') and retrieval_result.doc_indices:
                relevant_docs = [
                    rag.transformed_docs[doc_index]
                    for doc_index in retrieval_result.doc_indices
                    if doc_index < len(rag.transformed_docs)
                ]
            elif hasattr(retrieval_result, 'documents') and retrieval_result.documents:
                relevant_docs = retrieval_result.documents
            else:
                relevant_docs = []
            
            # Apply file type filter if specified
            if request.file_types:
                relevant_docs = [
                    doc for doc in relevant_docs
                    if any(doc.meta_data.get("file_path", "").endswith(ext) for ext in request.file_types)
                ]
            
            logger.info(f"Retrieved {len(relevant_docs)} relevant documents")
            
            # Step 4: Static code analysis (with caching)
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.ANALYZING,
                progress_percent=35,
                current_step="Analyzing code structure...",
                files_analyzed=0,
                total_files=len(relevant_docs)
            ))
            
            analyzer = get_analyzer(primary_language)
            
            # Generate cache key from file paths and contents
            cache_key = self._generate_analysis_cache_key(
                repo_url=request.repo_url,
                commit_hash=commit_hash,
                docs=relevant_docs
            )
            
            # Try to get from cache
            analysis_result = self.analysis_cache.get(cache_key)
            if analysis_result is None:
                analysis_result = await analyzer.analyze(
                    documents=relevant_docs,
                    repo_path=repo_path,
                    excluded_dirs=request.excluded_dirs,
                    excluded_files=request.excluded_files,
                    included_dirs=request.included_dirs,
                    included_files=request.included_files,
                    depth=request.depth
                )
                self.analysis_cache.set(cache_key, analysis_result)
                logger.info(f"Analyzed {len(analysis_result)} files (cached)")
            else:
                logger.info(f"Analysis cache hit: {len(analysis_result)} files")
            
            # Step 5: LLM relationship extraction
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.GENERATING,
                progress_percent=50,
                current_step="Inferring relationships...",
                files_analyzed=len(analysis_result)
            ))
            
            llm_relationships = await self.relationship_extractor.extract(
                query=request.query,
                analysis=analysis_result,
                query_intent=query_intent
            )
            
            # Step 6: Build graph
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.GENERATING,
                progress_percent=65,
                current_step="Building graph...",
            ))
            
            nodes = self.node_builder.build(analysis_result, query_intent)
            edges = self.edge_builder.build(analysis_result, llm_relationships)
            
            # Step 7: Prune and cluster
            nodes, edges = self.pruner.prune(
                nodes=nodes,
                edges=edges,
                query_intent=query_intent,
                max_nodes=request.max_nodes
            )
            
            clusters = self.clusterer.cluster(nodes, edges)
            
            # Step 8: Calculate layout
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.RENDERING,
                progress_percent=75,
                current_step="Calculating layout...",
                nodes_found=len(nodes),
                edges_found=len(edges)
            ))
            
            nodes = self.layout_engine.calculate(
                nodes=nodes,
                edges=edges,
                layout_type=query_intent.preferred_layout
            )
            
            graph = CodemapGraph(
                nodes=nodes,
                edges=edges,
                root_nodes=[n.id for n in nodes if n.parent_id is None][:5],
                clusters=clusters
            )
            
            # Step 9: Render outputs
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.RENDERING,
                progress_percent=85,
                current_step="Rendering diagram...",
            ))
            
            mermaid_code = self.mermaid_renderer.render(graph, query_intent)
            json_graph = self.json_renderer.render(graph)
            
            # Step 10: Generate trace guide
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.RENDERING,
                progress_percent=95,
                current_step="Writing trace guide...",
            ))
            
            trace_guide = await self.trace_writer.write(
                query=request.query,
                language=request.language or "en",
                graph=graph,
                analysis=analysis_result,
                query_intent=query_intent
            )
            
            # Build final codemap
            end_time = datetime.utcnow()
            generation_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            codemap = Codemap(
                id=codemap_id,
                repo_url=request.repo_url,
                repo_owner=repo_info["owner"],
                repo_name=repo_info["name"],
                commit_hash=commit_hash,
                query=request.query,
                analysis_type=analysis_type,
                title=self._generate_title(request.query, query_intent),
                description=trace_guide.summary,
                graph=graph,
                trace_guide=trace_guide,
                render=CodemapRenderOutput(
                    mermaid=mermaid_code,
                    json_graph=json_graph
                ),
                status=CodemapStatus.COMPLETED,
                generation_time_ms=generation_time_ms,
                model_used=self.model or "default"
            )
            
            # Save to storage
            await self.storage.save(codemap)
            
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.COMPLETED,
                progress_percent=100,
                current_step="Complete!",
                nodes_found=len(nodes),
                edges_found=len(edges)
            ))
            
            return codemap
            
        except Exception as e:
            logger.error(f"Codemap generation failed: {e}", exc_info=True)
            await self._emit_progress(progress_callback, CodemapProgress(
                codemap_id=codemap_id,
                status=CodemapStatus.FAILED,
                progress_percent=0,
                current_step="Failed",
                details=str(e)
            ))
            raise
    
    async def _emit_progress(
        self,
        callback: Optional[Callable[[CodemapProgress], None]],
        progress: CodemapProgress
    ):
        """Emit progress update if callback provided"""
        if callback:
            if asyncio.iscoroutinefunction(callback):
                await callback(progress)
            else:
                callback(progress)
    
    def _parse_repo_url(self, url: str) -> Dict[str, str]:
        """Parse repository URL to extract owner and name"""
        # Remove trailing .git if present
        url = url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        
        # Extract parts
        parts = url.split('/')
        if len(parts) >= 2:
            return {
                "owner": parts[-2],
                "name": parts[-1]
            }
        return {"owner": "unknown", "name": "unknown"}
    
    def _get_repo_head_hash(self, repo_path: str) -> Optional[str]:
        """Get git HEAD hash for the cloned repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()[:12]
        except Exception:
            pass
        return None
    
    def _detect_language(self, repo_path: str, docs: list) -> str:
        """Detect primary programming language"""
        ext_counts = {}
        
        for doc in docs:
            file_path = doc.meta_data.get("file_path", "")
            ext = os.path.splitext(file_path)[1].lower()
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        
        # Map extensions to languages
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.php': 'php',
        }
        
        # Find most common
        if ext_counts:
            most_common_ext = max(ext_counts.keys(), key=lambda x: ext_counts[x])
            return ext_to_lang.get(most_common_ext, 'unknown')
        
        return 'unknown'
    
    def _generate_analysis_cache_key(
        self, 
        repo_url: str, 
        commit_hash: Optional[str],
        docs: list
    ) -> str:
        """Generate a cache key for analysis results based on repo and file contents."""
        # Combine repo URL, commit hash, and sorted file paths
        file_paths = sorted([doc.meta_data.get("file_path", "") for doc in docs])
        key_content = f"{repo_url}:{commit_hash or 'no-commit'}:{':'.join(file_paths)}"
        return hashlib.md5(key_content.encode()).hexdigest()
    
    def _generate_title(self, query: str, query_intent: QueryIntent) -> str:
        """Generate a title for the codemap"""
        # Use first few words of query
        words = query.split()[:6]
        title = " ".join(words)
        if len(query.split()) > 6:
            title += "..."
        return title.title()
