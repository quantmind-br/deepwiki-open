"""
Storage layer for persisting codemaps.
"""

import os
import json
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from adalflow.utils import get_adalflow_default_root_path

from .models import Codemap

logger = logging.getLogger(__name__)

# Configurable share token TTL (in days)
SHARE_TOKEN_TTL_DAYS = 30


class CodemapStorage:
    """
    Handles persistence of codemap artifacts.
    
    Stores codemaps as JSON files in the ~/.adalflow/codemaps/ directory.
    """
    
    def __init__(self):
        self.storage_dir = os.path.join(get_adalflow_default_root_path(), "codemaps")
        os.makedirs(self.storage_dir, exist_ok=True)
    
    async def save(self, codemap: Codemap) -> bool:
        """
        Save a codemap to storage.
        
        Args:
            codemap: The codemap to save
            
        Returns:
            True if successful
        """
        try:
            file_path = self._get_file_path(codemap.id)
            
            # Convert to dict and handle datetime serialization
            data = codemap.model_dump()
            data['created_at'] = codemap.created_at.isoformat()
            data['updated_at'] = codemap.updated_at.isoformat()
            if codemap.share_expires_at:
                data['share_expires_at'] = codemap.share_expires_at.isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved codemap {codemap.id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving codemap {codemap.id}: {e}")
            return False
    
    async def load(self, codemap_id: str) -> Optional[Codemap]:
        """
        Load a codemap from storage.
        
        Args:
            codemap_id: The ID of the codemap to load
            
        Returns:
            Codemap object or None if not found
        """
        try:
            file_path = self._get_file_path(codemap_id)
            
            if not os.path.exists(file_path):
                logger.warning(f"Codemap {codemap_id} not found")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle datetime deserialization
            if isinstance(data.get('created_at'), str):
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if isinstance(data.get('updated_at'), str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            return Codemap(**data)
            
        except Exception as e:
            logger.error(f"Error loading codemap {codemap_id}: {e}")
            return None
    
    async def delete(self, codemap_id: str) -> bool:
        """
        Delete a codemap from storage.
        
        Args:
            codemap_id: The ID of the codemap to delete
            
        Returns:
            True if successful
        """
        try:
            file_path = self._get_file_path(codemap_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted codemap {codemap_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting codemap {codemap_id}: {e}")
            return False
    
    async def list_codemaps(
        self,
        repo_url: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        List stored codemaps.
        
        Args:
            repo_url: Optional filter by repository URL
            limit: Maximum number of results
            
        Returns:
            List of codemap metadata dicts
        """
        try:
            codemaps = []
            
            for filename in os.listdir(self.storage_dir):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.storage_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Filter by repo if specified
                    if repo_url and data.get('repo_url') != repo_url:
                        continue
                    
                    # Return metadata only
                    codemaps.append({
                        'id': data.get('id'),
                        'title': data.get('title'),
                        'query': data.get('query'),
                        'repo_url': data.get('repo_url'),
                        'repo_owner': data.get('repo_owner'),
                        'repo_name': data.get('repo_name'),
                        'status': data.get('status'),
                        'created_at': data.get('created_at'),
                        'is_public': data.get('is_public', False),
                    })
                    
                except Exception as e:
                    logger.warning(f"Error reading {filename}: {e}")
                    continue
            
            # Sort by created_at descending
            codemaps.sort(
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
            
            return codemaps[:limit]
            
        except Exception as e:
            logger.error(f"Error listing codemaps: {e}")
            return []
    
    async def get_by_repo(
        self,
        repo_owner: str,
        repo_name: str,
        limit: int = 20
    ) -> List[dict]:
        """
        Get codemaps for a specific repository.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            limit: Maximum results
            
        Returns:
            List of codemap metadata
        """
        all_codemaps = await self.list_codemaps(limit=1000)
        
        filtered = [
            cm for cm in all_codemaps
            if cm.get('repo_owner') == repo_owner and cm.get('repo_name') == repo_name
        ]
        
        return filtered[:limit]
    
    def _get_file_path(self, codemap_id: str) -> str:
        """Get the file path for a codemap"""
        # Sanitize ID for filesystem
        safe_id = "".join(c for c in codemap_id if c.isalnum() or c in '-_')
        return os.path.join(self.storage_dir, f"{safe_id}.json")
    
    async def update_share_token(
        self,
        codemap_id: str,
        share_token: str,
        is_public: bool = True,
        ttl_days: int = SHARE_TOKEN_TTL_DAYS
    ) -> bool:
        """
        Update the share token for a codemap with expiry.
        
        Args:
            codemap_id: Codemap ID
            share_token: New share token
            is_public: Whether the codemap should be public
            ttl_days: Number of days until the share token expires
            
        Returns:
            True if successful
        """
        codemap = await self.load(codemap_id)
        if not codemap:
            return False
        
        codemap.share_token = share_token
        codemap.is_public = is_public
        codemap.share_expires_at = datetime.utcnow() + timedelta(days=ttl_days)
        codemap.updated_at = datetime.utcnow()
        
        return await self.save(codemap)
    
    async def get_by_share_token(self, share_token: str) -> Optional[Codemap]:
        """
        Get a codemap by its share token, checking expiry.
        
        Args:
            share_token: The share token to search for
            
        Returns:
            Codemap if found and not expired, None otherwise
        """
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith('.json'):
                continue
            
            file_path = os.path.join(self.storage_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get('share_token') != share_token:
                    continue
                
                # Check if token has expired
                expires_at = data.get('share_expires_at')
                if expires_at:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at)
                    if datetime.utcnow() > expires_at:
                        logger.info(f"Share token expired for codemap {data.get('id')}")
                        return None
                
                # Handle datetime deserialization
                if isinstance(data.get('created_at'), str):
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                if isinstance(data.get('updated_at'), str):
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                if isinstance(data.get('share_expires_at'), str):
                    data['share_expires_at'] = datetime.fromisoformat(data['share_expires_at'])
                
                return Codemap(**data)
                
            except Exception as e:
                logger.warning(f"Error reading {filename}: {e}")
                continue
        
        return None
