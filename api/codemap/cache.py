"""
Caching layer for codemap analysis results.
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from adalflow.utils import get_adalflow_default_root_path

logger = logging.getLogger(__name__)


class AnalysisCache:
    """
    Cache for analysis results to avoid re-analyzing unchanged files.
    
    Uses file-based caching with content hashing for invalidation.
    """
    
    def __init__(self, ttl_hours: int = 24):
        self.cache_dir = os.path.join(
            get_adalflow_default_root_path(),
            "cache",
            "codemap_analysis"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def _get_cache_key(self, repo_url: str, file_path: str, content_hash: str) -> str:
        """Generate cache key from repo, file, and content hash."""
        combined = f"{repo_url}:{file_path}:{content_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get filesystem path for cache entry."""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(
        self,
        cache_key: str,
        repo_url: str = None,
        file_path: str = None,
        content_hash: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis result if available and not expired.
        
        Args:
            cache_key: Pre-computed cache key (for batch caching)
            repo_url: Repository URL (optional, for per-file caching)
            file_path: File path within the repository (optional)
            content_hash: Hash of the file content (optional)
            
        Returns:
            Cached result dict or None if not found/expired
        """
        # If all per-file args provided, compute key from them
        if repo_url and file_path and content_hash:
            cache_key = self._get_cache_key(repo_url, file_path, content_hash)
        cache_path = self._get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check expiry
            cached_at_str = data.get('cached_at')
            if cached_at_str:
                cached_at = datetime.fromisoformat(cached_at_str)
                if datetime.utcnow() - cached_at > self.ttl:
                    logger.debug(f"Cache expired for {file_path}")
                    os.remove(cache_path)
                    return None
            
            logger.debug(f"Cache hit for {file_path}")
            return data.get('result')
            
        except Exception as e:
            logger.warning(f"Cache read error for {file_path}: {e}")
            return None
    
    def set(
        self,
        cache_key: str,
        result: Dict[str, Any],
        repo_url: str = None,
        file_path: str = None,
        content_hash: str = None
    ) -> bool:
        """
        Store analysis result in cache.
        
        Args:
            cache_key: Pre-computed cache key (for batch caching)
            result: Analysis result to cache
            repo_url: Repository URL (optional, for per-file caching)
            file_path: File path within the repository (optional)
            content_hash: Hash of the file content (optional)
            
        Returns:
            True if successfully cached
        """
        # If all per-file args provided, compute key from them
        if repo_url and file_path and content_hash:
            cache_key = self._get_cache_key(repo_url, file_path, content_hash)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            data = {
                'cached_at': datetime.utcnow().isoformat(),
                'repo_url': repo_url,
                'file_path': file_path,
                'content_hash': content_hash,
                'result': result
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            logger.debug(f"Cached analysis for {file_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Cache write error for {file_path}: {e}")
            return False
    
    def invalidate(self, repo_url: str, file_path: Optional[str] = None) -> int:
        """
        Invalidate cache entries for a repository or specific file.
        
        Args:
            repo_url: Repository URL
            file_path: Optional specific file path
            
        Returns:
            Number of entries invalidated
        """
        invalidated = 0
        
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
            
            file_path_full = os.path.join(self.cache_dir, filename)
            
            try:
                with open(file_path_full, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get('repo_url') != repo_url:
                    continue
                
                if file_path and data.get('file_path') != file_path:
                    continue
                
                os.remove(file_path_full)
                invalidated += 1
                
            except Exception as e:
                logger.warning(f"Error invalidating {filename}: {e}")
                continue
        
        logger.info(f"Invalidated {invalidated} cache entries for {repo_url}")
        return invalidated
    
    def clear(self, max_age_days: int = 7) -> int:
        """
        Clear cache entries older than max_age_days.
        
        Args:
            max_age_days: Maximum age of cache entries in days
            
        Returns:
            Number of entries removed
        """
        max_age = timedelta(days=max_age_days)
        now = datetime.utcnow()
        removed = 0
        
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
            
            file_path = os.path.join(self.cache_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                cached_at_str = data.get('cached_at')
                if cached_at_str:
                    cached_at = datetime.fromisoformat(cached_at_str)
                    if now - cached_at > max_age:
                        os.remove(file_path)
                        removed += 1
                        
            except Exception as e:
                # Remove corrupted cache files
                logger.warning(f"Removing corrupted cache file {filename}: {e}")
                try:
                    os.remove(file_path)
                    removed += 1
                except:
                    pass
        
        logger.info(f"Cleared {removed} expired cache entries")
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        total_entries = 0
        total_size = 0
        oldest_entry = None
        newest_entry = None
        
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
            
            file_path = os.path.join(self.cache_dir, filename)
            total_entries += 1
            total_size += os.path.getsize(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                cached_at_str = data.get('cached_at')
                if cached_at_str:
                    cached_at = datetime.fromisoformat(cached_at_str)
                    if oldest_entry is None or cached_at < oldest_entry:
                        oldest_entry = cached_at
                    if newest_entry is None or cached_at > newest_entry:
                        newest_entry = cached_at
                        
            except Exception:
                pass
        
        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_entry': oldest_entry.isoformat() if oldest_entry else None,
            'newest_entry': newest_entry.isoformat() if newest_entry else None,
            'cache_dir': self.cache_dir,
            'ttl_hours': self.ttl.total_seconds() / 3600
        }


def get_content_hash(content: str) -> str:
    """
    Generate a hash for file content.
    
    Args:
        content: File content as string
        
    Returns:
        SHA256 hash truncated to 16 characters
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]
