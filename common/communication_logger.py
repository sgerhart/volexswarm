"""
Agent Communication Logger for VolexSwarm
Provides comprehensive logging of all agent-to-agent communications.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import text

from .db import get_db_client
from .config_manager import config_manager
from .logging import get_logger

logger = get_logger("communication_logger")

class CommunicationType(Enum):
    """Types of agent communications."""
    WEBSOCKET = "websocket"
    HTTP_API = "http_api"
    DATABASE = "database"
    INTERNAL = "internal"

class CommunicationDirection(Enum):
    """Direction of communication."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"

class CommunicationStatus(Enum):
    """Status of communication."""
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class CommunicationLog:
    """Data structure for communication log entry."""
    communication_id: str
    conversation_id: Optional[str]
    from_agent: str
    to_agent: str
    message_type: str
    direction: str
    message_content: Dict[str, Any]
    message_size: Optional[int]
    response_time_ms: Optional[int]
    status: str
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime

@dataclass
class ConversationLog:
    """Data structure for conversation log entry."""
    conversation_id: str
    topic: str
    participants: List[str]
    initiator: str
    status: str
    message_count: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    outcome: Optional[str]
    summary: Optional[str]
    metadata: Optional[Dict[str, Any]]

@dataclass
class AIInteractionLog:
    """Data structure for AI interaction log entry."""
    interaction_id: str
    conversation_id: Optional[str]
    agent_name: str
    interaction_type: str
    ai_model: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    response_time_ms: Optional[int]
    confidence_score: Optional[float]
    reasoning: Optional[str]
    decision: Optional[str]
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime

class AgentCommunicationLogger:
    """Comprehensive logger for agent communications."""
    
    def __init__(self):
        self.db_client = None
        self.logging_enabled = True
        self.websocket_logging_enabled = True
        self.api_call_logging_enabled = True
        self.ai_interaction_logging_enabled = True
        self.log_message_content = True
        self.log_ai_prompts = True
        self.active_conversations: Dict[str, ConversationLog] = {}
        self.conversation_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the communication logger."""
        try:
            self.db_client = get_db_client()
            
            # Load configuration - handle missing method gracefully
            try:
                config = await config_manager.get_system_config()
            except AttributeError:
                # Fallback to default configuration if method doesn't exist
                config = {
                    'communication_logging_enabled': 'true',
                    'websocket_logging_enabled': 'true',
                    'api_call_logging_enabled': 'true',
                    'ai_interaction_logging_enabled': 'true',
                    'log_message_content': 'true',
                    'log_ai_prompts': 'true'
                }
            
            self.logging_enabled = config.get('communication_logging_enabled', 'true').lower() == 'true'
            self.websocket_logging_enabled = config.get('websocket_logging_enabled', 'true').lower() == 'true'
            self.api_call_logging_enabled = config.get('api_call_logging_enabled', 'true').lower() == 'true'
            self.ai_interaction_logging_enabled = config.get('ai_interaction_logging_enabled', 'true').lower() == 'true'
            self.log_message_content = config.get('log_message_content', 'true').lower() == 'true'
            self.log_ai_prompts = config.get('log_ai_prompts', 'true').lower() == 'true'
            
            logger.info("Agent Communication Logger initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize communication logger: {e}")
            self.logging_enabled = False
    
    async def log_websocket_message(self, 
                                  from_agent: str,
                                  to_agent: str,
                                  message_type: str,
                                  direction: str,
                                  message_data: Dict[str, Any],
                                  conversation_id: Optional[str] = None,
                                  connection_id: Optional[str] = None,
                                  session_id: Optional[str] = None,
                                  response_time_ms: Optional[int] = None,
                                  status: str = "sent",
                                  error_message: Optional[str] = None,
                                  metadata: Optional[Dict[str, Any]] = None):
        """Log a WebSocket message between agents."""
        if not self.logging_enabled or not self.websocket_logging_enabled:
            return
        
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Prepare message content
            if self.log_message_content:
                message_content = message_data
            else:
                message_content = {"message_type": message_type, "size": len(json.dumps(message_data))}
            
            # Create log entry
            log_entry = {
                "timestamp": timestamp,
                "message_id": message_id,
                "conversation_id": conversation_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message_type": message_type,
                "direction": direction,
                "message_data": message_content,
                "message_size": len(json.dumps(message_data)),
                "connection_id": connection_id,
                "session_id": session_id,
                "response_time_ms": response_time_ms,
                "status": status,
                "error_message": error_message,
                "metadata": metadata or {},
                "created_at": timestamp
            }
            
            # Insert into database
            await self._insert_websocket_message(log_entry)
            
            # Update conversation if applicable
            if conversation_id:
                await self._update_conversation_message_count(conversation_id)
            
            logger.debug(f"Logged WebSocket message: {from_agent} -> {to_agent} ({message_type})")
            
        except Exception as e:
            logger.error(f"Failed to log WebSocket message: {e}")
    
    async def log_api_call(self,
                          from_agent: str,
                          to_agent: str,
                          endpoint: str,
                          method: str,
                          request_data: Optional[Dict[str, Any]] = None,
                          response_data: Optional[Dict[str, Any]] = None,
                          response_code: Optional[int] = None,
                          response_time_ms: Optional[int] = None,
                          conversation_id: Optional[str] = None,
                          status: str = "success",
                          error_message: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """Log an API call between agents."""
        if not self.logging_enabled or not self.api_call_logging_enabled:
            return
        
        try:
            call_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Prepare request/response content
            if self.log_message_content:
                request_content = request_data
                response_content = response_data
            else:
                request_content = {"endpoint": endpoint, "method": method, "size": len(json.dumps(request_data)) if request_data else 0}
                response_content = {"response_code": response_code, "size": len(json.dumps(response_data)) if response_data else 0}
            
            # Create log entry
            log_entry = {
                "timestamp": timestamp,
                "call_id": call_id,
                "conversation_id": conversation_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "endpoint": endpoint,
                "method": method,
                "request_data": request_content,
                "response_data": response_content,
                "response_code": response_code,
                "response_time_ms": response_time_ms,
                "status": status,
                "error_message": error_message,
                "metadata": metadata or {},
                "created_at": timestamp
            }
            
            # Insert into database
            await self._insert_api_call(log_entry)
            
            # Update conversation if applicable
            if conversation_id:
                await self._update_conversation_message_count(conversation_id)
            
            logger.debug(f"Logged API call: {from_agent} -> {to_agent} ({method} {endpoint})")
            
        except Exception as e:
            logger.error(f"Failed to log API call: {e}")
    
    async def log_ai_interaction(self,
                                agent_name: str,
                                interaction_type: str,
                                ai_model: str,
                                prompt_tokens: Optional[int] = None,
                                completion_tokens: Optional[int] = None,
                                total_tokens: Optional[int] = None,
                                response_time_ms: Optional[int] = None,
                                confidence_score: Optional[float] = None,
                                reasoning: Optional[str] = None,
                                decision: Optional[str] = None,
                                conversation_id: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None):
        """Log an AI interaction."""
        if not self.logging_enabled or not self.ai_interaction_logging_enabled:
            return
        
        try:
            interaction_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Prepare reasoning content
            if not self.log_ai_prompts:
                reasoning = "AI reasoning logged (content hidden for privacy)"
            
            # Create log entry
            log_entry = {
                "timestamp": timestamp,
                "interaction_id": interaction_id,
                "conversation_id": conversation_id,
                "agent_name": agent_name,
                "interaction_type": interaction_type,
                "ai_model": ai_model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "response_time_ms": response_time_ms,
                "confidence_score": confidence_score,
                "reasoning": reasoning,
                "decision": decision,
                "metadata": metadata or {},
                "created_at": timestamp
            }
            
            # Insert into database
            await self._insert_ai_interaction(log_entry)
            
            logger.debug(f"Logged AI interaction: {agent_name} ({interaction_type})")
            
        except Exception as e:
            logger.error(f"Failed to log AI interaction: {e}")
    
    async def start_conversation(self,
                                conversation_id: str,
                                topic: str,
                                participants: List[str],
                                initiator: str,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Start a new conversation."""
        if not self.logging_enabled:
            return False
        
        try:
            async with self.conversation_lock:
                start_time = datetime.now()
                
                conversation = ConversationLog(
                    conversation_id=conversation_id,
                    topic=topic,
                    participants=participants,
                    initiator=initiator,
                    status="active",
                    message_count=0,
                    start_time=start_time,
                    end_time=None,
                    duration_seconds=None,
                    outcome=None,
                    summary=None,
                    metadata=metadata or {}
                )
                
                # Store in memory
                self.active_conversations[conversation_id] = conversation
                
                # Insert into database
                await self._insert_conversation(asdict(conversation))
                
                logger.info(f"Started conversation: {conversation_id} ({topic}) initiated by {initiator}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            return False
    
    async def end_conversation(self,
                              conversation_id: str,
                              outcome: str,
                              summary: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """End an active conversation."""
        if not self.logging_enabled:
            return False
        
        try:
            async with self.conversation_lock:
                if conversation_id not in self.active_conversations:
                    logger.warning(f"Conversation {conversation_id} not found in active conversations")
                    return False
                
                conversation = self.active_conversations[conversation_id]
                end_time = datetime.now()
                duration_seconds = int((end_time - conversation.start_time).total_seconds())
                
                # Update conversation
                conversation.end_time = end_time
                conversation.duration_seconds = duration_seconds
                conversation.outcome = outcome
                conversation.status = "completed"
                if summary:
                    conversation.summary = summary
                if metadata:
                    conversation.metadata.update(metadata)
                
                # Update in database
                await self._update_conversation(asdict(conversation))
                
                # Remove from active conversations
                del self.active_conversations[conversation_id]
                
                logger.info(f"Ended conversation: {conversation_id} ({outcome}) - Duration: {duration_seconds}s")
                return True
                
        except Exception as e:
            logger.error(f"Failed to end conversation: {e}")
            return False
    
    async def log_performance_metric(self,
                                   agent_name: str,
                                   metric_name: str,
                                   metric_value: float,
                                   metric_unit: Optional[str] = None,
                                   context: Optional[Dict[str, Any]] = None):
        """Log a performance metric for an agent."""
        if not self.logging_enabled:
            return
        
        try:
            timestamp = datetime.now()
            
            log_entry = {
                "timestamp": timestamp,
                "agent_name": agent_name,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metric_unit": metric_unit,
                "context": context or {},
                "created_at": timestamp
            }
            
            await self._insert_performance_metric(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")
    
    async def get_conversation_summary(self,
                                     period_start: datetime,
                                     period_end: datetime,
                                     period_type: str = "hourly") -> Dict[str, Any]:
        """Generate a summary of conversations for a time period."""
        try:
            # Query database for summary data
            query = """
            SELECT 
                COUNT(*) as total_conversations,
                COUNT(CASE WHEN outcome = 'success' THEN 1 END) as successful_conversations,
                COUNT(CASE WHEN outcome = 'failure' THEN 1 END) as failed_conversations,
                AVG(duration_seconds) as avg_duration_seconds,
                AVG(message_count) as avg_message_count,
                topic,
                initiator
            FROM agent_conversations 
            WHERE start_time >= %s AND start_time < %s
            GROUP BY topic, initiator
            ORDER BY total_conversations DESC
            """
            
            with self.db_client.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (period_start, period_end))
                    results = cursor.fetchall()
            
            return {
                "period_start": period_start,
                "period_end": period_end,
                "period_type": period_type,
                "total_conversations": sum(r['total_conversations'] for r in results),
                "successful_conversations": sum(r['successful_conversations'] for r in results),
                "failed_conversations": sum(r['failed_conversations'] for r in results),
                "avg_duration_seconds": sum(r['avg_duration_seconds'] or 0 for r in results) / len(results) if results else 0,
                "avg_message_count": sum(r['avg_message_count'] or 0 for r in results) / len(results) if results else 0,
                "topics": [{"topic": r['topic'], "count": r['total_conversations']} for r in results[:10]],
                "initiators": [{"initiator": r['initiator'], "count": r['total_conversations']} for r in results[:10]]
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return {}
    
    async def _insert_websocket_message(self, log_entry: Dict[str, Any]):
        """Insert WebSocket message log into database."""
        query = """
        INSERT INTO agent_websocket_messages (
            timestamp, message_id, conversation_id, from_agent, to_agent, 
            message_type, direction, message_data, message_size, connection_id, 
            session_id, response_time_ms, status, error_message, metadata, created_at
        ) VALUES (
            :timestamp, :message_id, :conversation_id, :from_agent, :to_agent,
            :message_type, :direction, :message_data, :message_size, :connection_id,
            :session_id, :response_time_ms, :status, :error_message, :metadata, :created_at
        )
        """
        
        # Convert dict fields to JSON strings
        if isinstance(log_entry.get('message_data'), dict):
            log_entry['message_data'] = json.dumps(log_entry['message_data'])
        if isinstance(log_entry.get('metadata'), dict):
            log_entry['metadata'] = json.dumps(log_entry['metadata'])
        
        with self.db_client.get_session() as session:
            session.execute(text(query), log_entry)
            session.commit()
    
    async def _insert_api_call(self, log_entry: Dict[str, Any]):
        """Insert API call log into database."""
        query = """
        INSERT INTO agent_api_calls (
            timestamp, call_id, conversation_id, from_agent, to_agent, endpoint, method,
            request_data, response_data, response_code, response_time_ms, status, 
            error_message, metadata, created_at
        ) VALUES (
            :timestamp, :call_id, :conversation_id, :from_agent, :to_agent,
            :endpoint, :method, :request_data, :response_data, :response_code,
            :response_time_ms, :status, :error_message, :metadata, :created_at
        )
        """
        
        # Convert dict fields to JSON strings
        if isinstance(log_entry.get('request_data'), dict):
            log_entry['request_data'] = json.dumps(log_entry['request_data'])
        if isinstance(log_entry.get('response_data'), dict):
            log_entry['response_data'] = json.dumps(log_entry['response_data'])
        if isinstance(log_entry.get('metadata'), dict):
            log_entry['metadata'] = json.dumps(log_entry['metadata'])
        
        with self.db_client.get_session() as session:
            session.execute(text(query), log_entry)
            session.commit()
    
    async def _insert_ai_interaction(self, log_entry: Dict[str, Any]):
        """Insert AI interaction log into database."""
        query = """
        INSERT INTO agent_ai_interactions (
            timestamp, interaction_id, conversation_id, agent_name, interaction_type,
            ai_model, prompt_tokens, completion_tokens, total_tokens, response_time_ms,
            confidence_score, reasoning, decision, metadata, created_at
        ) VALUES (
            :timestamp, :interaction_id, :conversation_id, :agent_name, :interaction_type,
            :ai_model, :prompt_tokens, :completion_tokens, :total_tokens, :response_time_ms,
            :confidence_score, :reasoning, :decision, :metadata, :created_at
        )
        """
        
        # Convert dict fields to JSON strings
        if isinstance(log_entry.get('metadata'), dict):
            log_entry['metadata'] = json.dumps(log_entry['metadata'])
        
        with self.db_client.get_session() as session:
            session.execute(text(query), log_entry)
            session.commit()
    
    async def _insert_conversation(self, log_entry: Dict[str, Any]):
        """Insert conversation log into database."""
        query = """
        INSERT INTO agent_conversations (
            conversation_id, topic, participants, initiator, status, message_count,
            start_time, end_time, duration_seconds, outcome, summary, metadata, created_at, updated_at
        ) VALUES (
            :conversation_id, :topic, :participants, :initiator, :status, :message_count,
            :start_time, :end_time, :duration_seconds, :outcome, :summary, :metadata, :created_at, :updated_at
        )
        """
        
        # Convert dict fields to JSON strings
        if isinstance(log_entry.get('participants'), list):
            log_entry['participants'] = json.dumps(log_entry['participants'])
        if isinstance(log_entry.get('metadata'), dict):
            log_entry['metadata'] = json.dumps(log_entry['metadata'])
        
        with self.db_client.get_session() as session:
            session.execute(text(query), log_entry)
            session.commit()
    
    async def _update_conversation(self, log_entry: Dict[str, Any]):
        """Update conversation log in database."""
        query = """
        UPDATE agent_conversations SET
            status = :status,
            message_count = :message_count,
            end_time = :end_time,
            duration_seconds = :duration_seconds,
            outcome = :outcome,
            summary = :summary,
            metadata = :metadata,
            updated_at = :updated_at
        WHERE conversation_id = :conversation_id
        """
        
        # Convert dict fields to JSON strings
        if isinstance(log_entry.get('metadata'), dict):
            log_entry['metadata'] = json.dumps(log_entry['metadata'])
        
        with self.db_client.get_session() as session:
            session.execute(text(query), log_entry)
            session.commit()
    
    async def _update_conversation_message_count(self, conversation_id: str):
        """Update message count for a conversation."""
        query = """
        UPDATE agent_conversations 
        SET message_count = message_count + 1, updated_at = CURRENT_TIMESTAMP
        WHERE conversation_id = :conversation_id
        """
        
        with self.db_client.get_session() as session:
            session.execute(text(query), {"conversation_id": conversation_id})
            session.commit()
    
    async def _insert_performance_metric(self, log_entry: Dict[str, Any]):
        """Insert performance metric log into database."""
        query = """
        INSERT INTO agent_performance_metrics (
            timestamp, agent_name, metric_name, metric_value, metric_unit, context, created_at
        ) VALUES (
            :timestamp, :agent_name, :metric_name, :metric_value, :metric_unit, :context, :created_at
        )
        """
        
        # Convert dict fields to JSON strings
        if isinstance(log_entry.get('context'), dict):
            log_entry['context'] = json.dumps(log_entry['context'])
        
        with self.db_client.get_session() as session:
            session.execute(text(query), log_entry)
            session.commit()

# Global communication logger instance
communication_logger = AgentCommunicationLogger()
