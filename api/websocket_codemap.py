"""
WebSocket handler for real-time codemap generation.
"""

import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from api.codemap.models import CodemapGenerateRequest, CodemapProgress, CodemapStatus
from api.codemap.engine import CodemapEngine

logger = logging.getLogger(__name__)


class CodemapWebSocketHandler:
    """
    WebSocket handler for real-time codemap generation.
    
    Protocol:
    1. Client connects to /ws/codemap
    2. Client sends CodemapGenerateRequest as JSON
    3. Server streams CodemapProgress updates
    4. Server sends final Codemap or error
    5. Connection closes
    """
    
    async def handle(self, websocket: WebSocket):
        """Handle a WebSocket connection for codemap generation"""
        await websocket.accept()
        
        try:
            # Receive generation request
            request_dict = await websocket.receive_json()
            
            try:
                request = CodemapGenerateRequest(**request_dict)
            except ValidationError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid request: {str(e)}"
                })
                await websocket.close()
                return
            
            logger.info(f"WebSocket codemap generation started for: {request.repo_url}")
            
            # Create engine
            engine = CodemapEngine(
                provider=request.provider or "google",
                model=request.model
            )
            
            # Progress callback
            async def send_progress(progress: CodemapProgress):
                try:
                    await websocket.send_json({
                        "type": "progress",
                        "data": progress.model_dump()
                    })
                except Exception as e:
                    logger.warning(f"Failed to send progress: {e}")
            
            # Generate codemap
            try:
                codemap = await engine.generate(
                    request=request,
                    progress_callback=send_progress
                )
                
                # Send final result
                await websocket.send_json({
                    "type": "complete",
                    "data": {
                        "id": codemap.id,
                        "title": codemap.title,
                        "description": codemap.description,
                        "query": codemap.query,
                        "repo_url": codemap.repo_url,
                        "repo_owner": codemap.repo_owner,
                        "repo_name": codemap.repo_name,
                        "status": codemap.status.value,
                        "generation_time_ms": codemap.generation_time_ms,
                        "graph": {
                            "nodes": [n.model_dump() for n in codemap.graph.nodes],
                            "edges": [e.model_dump() for e in codemap.graph.edges],
                            "root_nodes": codemap.graph.root_nodes,
                            "clusters": codemap.graph.clusters,
                        },
                        "trace_guide": {
                            "title": codemap.trace_guide.title,
                            "summary": codemap.trace_guide.summary,
                            "sections": [s.model_dump() for s in codemap.trace_guide.sections],
                            "conclusion": codemap.trace_guide.conclusion,
                        },
                        "render": {
                            "mermaid": codemap.render.mermaid,
                            "json_graph": codemap.render.json_graph,
                        },
                        "created_at": codemap.created_at.isoformat(),
                    }
                })
                
                logger.info(f"WebSocket codemap generation completed: {codemap.id}")
                
            except Exception as e:
                logger.error(f"Codemap generation error: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
        
        except WebSocketDisconnect:
            logger.info("Client disconnected from codemap WebSocket")
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid JSON"
            })
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
            except:
                pass
        finally:
            try:
                await websocket.close()
            except:
                pass


# Create handler instance
codemap_ws_handler = CodemapWebSocketHandler()


async def handle_websocket_codemap(websocket: WebSocket):
    """Handle WebSocket connection for codemap generation"""
    await codemap_ws_handler.handle(websocket)
