"""
VolexSwarm Redis Client - Caching, Session Storage, and Real-time Messaging
Provides Redis integration for caching, pub/sub messaging, and session management.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis
import pickle
import hashlib

# Initialize logger
logger = logging.getLogger(__name__)


class RedisManager:
    """Manages Redis connections and operations."""
    
    def __init__(self, host: str = "redis", port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, decode_responses: bool = True):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.redis_client: Optional[Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        
    async def connect(self) -> bool:
        """Establish connection to Redis."""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=self.decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            return False
    
    async def disconnect(self):
        """Close Redis connection."""
        try:
            if self.pubsub:
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("Disconnected from Redis")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            if not self.redis_client:
                return False
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    # Caching Operations
    async def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL."""
        try:
            if not self.redis_client:
                return False
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            if ttl:
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
            
            logger.debug(f"Cached key: {key} (TTL: {ttl})")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {str(e)}")
            return False
    
    async def get_cache(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        try:
            if not self.redis_client:
                return default
            
            value = await self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize as JSON first
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return value
            
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {str(e)}")
            return default
    
    async def delete_cache(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            if not self.redis_client:
                return False
            
            result = await self.redis_client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    async def clear_cache_pattern(self, pattern: str) -> int:
        """Clear cache keys matching a pattern."""
        try:
            if not self.redis_client:
                return 0
            
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
            return 0
    
    async def cache_exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            if not self.redis_client:
                return False
            
            return await self.redis_client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Error checking cache existence for key {key}: {str(e)}")
            return False
    
    # Session Management
    async def set_session(self, session_id: str, data: Dict[str, Any], 
                         ttl: int = 3600) -> bool:
        """Store session data."""
        try:
            key = f"session:{session_id}"
            return await self.set_cache(key, data, ttl)
        except Exception as e:
            logger.error(f"Error setting session {session_id}: {str(e)}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        try:
            key = f"session:{session_id}"
            return await self.get_cache(key)
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session data."""
        try:
            key = f"session:{session_id}"
            return await self.delete_cache(key)
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    # Pub/Sub Messaging
    async def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel."""
        try:
            if not self.redis_client:
                return 0
            
            if isinstance(message, (dict, list)):
                serialized_message = json.dumps(message)
            else:
                serialized_message = str(message)
            
            subscribers = await self.redis_client.publish(channel, serialized_message)
            logger.debug(f"Published message to channel {channel}: {subscribers} subscribers")
            return subscribers
            
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {str(e)}")
            return 0
    
    async def subscribe(self, channel: str, callback: Callable) -> bool:
        """Subscribe to a channel with a callback function."""
        try:
            if not self.redis_client:
                return False
            
            # Store callback for local subscribers
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(callback)
            
            # Subscribe to Redis channel
            if not self.pubsub:
                self.pubsub = self.redis_client.pubsub()
            
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel: {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {str(e)}")
            return False
    
    async def unsubscribe(self, channel: str) -> bool:
        """Unsubscribe from a channel."""
        try:
            if not self.pubsub:
                return False
            
            await self.pubsub.unsubscribe(channel)
            
            # Remove local callbacks
            if channel in self.subscribers:
                del self.subscribers[channel]
            
            logger.info(f"Unsubscribed from channel: {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from channel {channel}: {str(e)}")
            return False
    
    async def listen_for_messages(self):
        """Listen for messages on subscribed channels."""
        try:
            if not self.pubsub:
                return
            
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    # Try to parse as JSON
                    try:
                        parsed_data = json.loads(data)
                    except json.JSONDecodeError:
                        parsed_data = data
                    
                    # Call local subscribers
                    if channel in self.subscribers:
                        for callback in self.subscribers[channel]:
                            try:
                                await callback(channel, parsed_data)
                            except Exception as e:
                                logger.error(f"Error in subscriber callback: {str(e)}")
                    
                    logger.debug(f"Received message on {channel}: {parsed_data}")
                    
        except Exception as e:
            logger.error(f"Error listening for messages: {str(e)}")
    
    # Agent Communication
    async def send_agent_message(self, agent_name: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific agent."""
        try:
            channel = f"agent:{agent_name}"
            return await self.publish(channel, message) > 0
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_name}: {str(e)}")
            return False
    
    async def broadcast_system_message(self, message: Dict[str, Any]) -> bool:
        """Broadcast a message to all agents."""
        try:
            channel = "system:broadcast"
            return await self.publish(channel, message) > 0
        except Exception as e:
            logger.error(f"Error broadcasting system message: {str(e)}")
            return False
    
    # Rate Limiting
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if a rate limit has been exceeded."""
        try:
            if not self.redis_client:
                return True
            
            current = await self.redis_client.get(key)
            if current is None:
                await self.redis_client.setex(key, window, 1)
                return True
            
            current_count = int(current)
            if current_count >= limit:
                return False
            
            await self.redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit for key {key}: {str(e)}")
            return True
    
    # Data Structures
    async def add_to_list(self, key: str, value: Any, max_length: Optional[int] = None) -> bool:
        """Add a value to a Redis list."""
        try:
            if not self.redis_client:
                return False
            
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            await self.redis_client.lpush(key, serialized_value)
            
            # Trim list if max_length is specified
            if max_length:
                await self.redis_client.ltrim(key, 0, max_length - 1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding to list {key}: {str(e)}")
            return False
    
    async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get values from a Redis list."""
        try:
            if not self.redis_client:
                return []
            
            values = await self.redis_client.lrange(key, start, end)
            result = []
            
            for value in values:
                try:
                    result.append(json.loads(value))
                except json.JSONDecodeError:
                    result.append(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting list {key}: {str(e)}")
            return []
    
    async def add_to_set(self, key: str, value: Any) -> bool:
        """Add a value to a Redis set."""
        try:
            if not self.redis_client:
                return False
            
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            await self.redis_client.sadd(key, serialized_value)
            return True
            
        except Exception as e:
            logger.error(f"Error adding to set {key}: {str(e)}")
            return False
    
    async def get_set(self, key: str) -> List[Any]:
        """Get all values from a Redis set."""
        try:
            if not self.redis_client:
                return []
            
            values = await self.redis_client.smembers(key)
            result = []
            
            for value in values:
                try:
                    result.append(json.loads(value))
                except json.JSONDecodeError:
                    result.append(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting set {key}: {str(e)}")
            return []
    
    # Metrics and Monitoring
    async def get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server information."""
        try:
            if not self.redis_client:
                return {}
            
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis info: {str(e)}")
            return {}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if not self.redis_client:
                return {}
            
            # Get all keys
            all_keys = await self.redis_client.keys("*")
            
            # Count by pattern
            stats = {
                "total_keys": len(all_keys),
                "cache_keys": len([k for k in all_keys if k.startswith("cache:")]),
                "session_keys": len([k for k in all_keys if k.startswith("session:")]),
                "agent_keys": len([k for k in all_keys if k.startswith("agent:")]),
                "system_keys": len([k for k in all_keys if k.startswith("system:")])
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}


# Global Redis manager instance
_redis_manager: Optional[RedisManager] = None


async def get_redis_client() -> RedisManager:
    """Get the global Redis client instance."""
    global _redis_manager
    
    if _redis_manager is None:
        # Get Redis configuration from environment
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD")
        
        _redis_manager = RedisManager(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password
        )
        
        # Connect to Redis
        if not await _redis_manager.connect():
            logger.error("Failed to connect to Redis")
            raise ConnectionError("Failed to connect to Redis")
    
    return _redis_manager


async def close_redis_client():
    """Close the global Redis client connection."""
    global _redis_manager
    
    if _redis_manager:
        await _redis_manager.disconnect()
        _redis_manager = None


# Convenience functions for common operations
async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set a value in cache."""
    client = await get_redis_client()
    return await client.set_cache(key, value, ttl)


async def cache_get(key: str, default: Any = None) -> Any:
    """Get a value from cache."""
    client = await get_redis_client()
    return await client.get_cache(key, default)


async def cache_delete(key: str) -> bool:
    """Delete a key from cache."""
    client = await get_redis_client()
    return await client.delete_cache(key)


async def publish_message(channel: str, message: Any) -> int:
    """Publish a message to a channel."""
    client = await get_redis_client()
    return await client.publish(channel, message)


async def send_agent_message(agent_name: str, message: Dict[str, Any]) -> bool:
    """Send a message to a specific agent."""
    client = await get_redis_client()
    return await client.send_agent_message(agent_name, message)


async def broadcast_system_message(message: Dict[str, Any]) -> bool:
    """Broadcast a message to all agents."""
    client = await get_redis_client()
    return await client.broadcast_system_message(message) 