#!/usr/bin/env python3
"""
⚠️  DEPRECATED - VolexSwarm Agentic Meta Agent ⚠️

This file is DEPRECATED and no longer used in the active system.
The system now uses the enhanced `hybrid_meta_agent.py` instead.

REASON FOR DEPRECATION:
- This was a massive 4,449-line file that became unmaintainable
- Too many features and phases made it complex and error-prone
- The active system uses `hybrid_meta_agent.py` with streamlined features
- All essential functionality has been preserved and enhanced in the active agent

CURRENT ACTIVE AGENT:
- File: `hybrid_meta_agent.py` 
- Main entry point: `main.py`
- Status: Enhanced with portfolio intelligence, AutoGen integration, and critical features restored

FILE STATS:
- Lines: 4,449 (excessive complexity)
- Status: DEPRECATED - DO NOT USE
- Kept for: Reference and historical purposes only

DO NOT USE THIS FILE - It is kept for reference only.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import websockets
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import threading
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import JSONResponse

import uvicorn

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.agentic_framework.agent_templates import MetaAgent
from agents.agentic_framework.mcp_tools import MCPToolRegistry
from agents.agentic_framework.agent_coordinator import EnhancedAgentCoordinator as AgentCoordinator
from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client
from common.logging import get_logger
from common.models import Strategy, Trade, Signal, AgentLog
from common.openai_client import get_openai_client

logger = get_logger("agentic_meta")

class TaskPriority(Enum):
    """Task priority levels for intelligent scheduling."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    """Task status tracking."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    """Intelligent task definition with metadata."""
    id: str
    name: str
    description: str
    priority: TaskPriority
    assigned_agents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentConsensus:
    """Consensus mechanism for agent decisions."""
    task_id: str
    agents: List[str]
    decision: str
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    votes: Dict[str, str] = field(default_factory=dict)

@dataclass
class AutonomousDecision:
    """Autonomous decision with validation and learning capabilities."""
    id: str
    decision_type: str
    context: Dict[str, Any]
    decision: str
    confidence: float
    reasoning: str
    alternatives: List[str]
    validation_status: str = "pending"
    validation_score: float = 0.0
    learning_feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionValidation:
    """Decision validation results."""
    decision_id: str
    validation_method: str
    score: float
    feedback: str
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class AgenticMetaAgent(MetaAgent):
    """Intelligent Meta Agent with AutoGen GroupChatManager capabilities."""

    def __init__(self, llm_config: Dict[str, Any] = None, tool_registry: MCPToolRegistry = None):
        # Initialize with placeholder config - real API key will be loaded from Vault
        if llm_config is None:
            logger.info("Initializing with placeholder config. OpenAI API key will be loaded from Vault during initialize().")
            # Use a placeholder config that satisfies AutoGen validation
            # The real API key will be loaded from Vault during initialize()
            default_llm_config = {
                "config_list": [{
                    "api_type": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "placeholder-key-will-be-replaced-from-vault"
                }],
                "temperature": 0.7
            }
            llm_config = default_llm_config
        
        super().__init__(llm_config)
        # Assign MCP tools directly if not provided by coordinator
        if tool_registry is None:
            from agents.agentic_framework.mcp_tools import create_mcp_tool_registry
            tool_registry = create_mcp_tool_registry()
        self.tool_registry = tool_registry
        
        # Initialize intelligent coordination systems
        self.tasks: Dict[str, Task] = {}
        self.agent_consensus: Dict[str, AgentConsensus] = {}
        
        # Initialize autonomous decision making systems
        self.autonomous_decisions: Dict[str, AutonomousDecision] = {}
        self.decision_history: List[AutonomousDecision] = []
        self.decision_validation: Dict[str, DecisionValidation] = {}
        self.decision_learning: Dict[str, Dict[str, Any]] = {}
        
        # Initialize agent self-direction systems
        self.agent_goals: Dict[str, Dict[str, Any]] = {}
        self.self_monitoring_data: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        self.learning_progress: Dict[str, Dict[str, Any]] = {}
        
        # Initialize creative problem solving systems
        self.creative_solutions: Dict[str, Dict[str, Any]] = {}
        self.innovation_history: List[Dict[str, Any]] = []
        self.adaptive_strategies: Dict[str, Dict[str, Any]] = {}
        self.novel_approaches: List[Dict[str, Any]] = []
        self.creative_learning: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Phase 6.1 Advanced Automation systems
        self.automation_workflows: Dict[str, Dict[str, Any]] = {}
        self.task_scheduler: Dict[str, Dict[str, Any]] = {}
        self.resource_optimizer: Dict[str, Dict[str, Any]] = {}
        self.system_orchestrator: Dict[str, Dict[str, Any]] = {}
        self.automation_history: List[Dict[str, Any]] = []
        
        # Initialize Phase 6.2 Intelligent Workflows systems
        self.intelligent_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_optimizer: Dict[str, Dict[str, Any]] = {}
        self.workflow_monitor: Dict[str, Dict[str, Any]] = {}
        self.workflow_learning: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
        # Initialize Phase 6.3 System Self-Healing systems
        self.fault_detector: Dict[str, Dict[str, Any]] = {}
        self.recovery_manager: Dict[str, Dict[str, Any]] = {}
        self.health_monitor: Dict[str, Dict[str, Any]] = {}
        self.preventive_maintenance: Dict[str, Dict[str, Any]] = {}
        self.system_resilience: Dict[str, Dict[str, Any]] = {}
        self.self_healing_history: List[Dict[str, Any]] = []
        
        # Initialize Phase 7.1 Security Enhancement systems
        self.security_manager: Dict[str, Dict[str, Any]] = {}
        self.authentication_system: Dict[str, Dict[str, Any]] = {}
        self.authorization_system: Dict[str, Dict[str, Any]] = {}
        self.audit_system: Dict[str, Dict[str, Any]] = {}
        self.encryption_system: Dict[str, Dict[str, Any]] = {}
        self.security_history: List[Dict[str, Any]] = []
        
        # Initialize missing attributes that are referenced in methods
        self.conflict_resolution_history: List[Dict[str, Any]] = []
        self.autonomous_decisions: Dict[str, AutonomousDecision] = {}
        self.decision_history: List[AutonomousDecision] = []
        self.decision_validation: Dict[str, DecisionValidation] = {}
        self.agent_loads: Dict[str, int] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.agent_consensus: Dict[str, AgentConsensus] = {}
        self.websocket_clients: set = set()
        self.agent_coordinator = None
        
        # Initialize missing attributes that are referenced in methods
        self.agent: Optional[Any] = None
        self.agent_goals: Dict[str, Dict[str, Any]] = {}
        self.self_monitoring_data: Dict[str, Dict[str, Any]] = {}
        
        # Initialize infrastructure attributes for test compatibility
        self.vault_client = None
        self.db_client = None
        self.openai_client = None
        
        # Initialize server attributes
        self.websocket_port = 8012  # WebSocket on port 8012
        self.api_port = 8004        # FastAPI on port 8004
        self.connected_agents = set()  # Initialize connected agents set
        self.active_tasks = set()      # Initialize active tasks set
        
        # Initialize FastAPI app
        from fastapi import FastAPI
        self.fastapi_app = FastAPI(title="VolexSwarm Meta Agent API")
        
        
        self._setup_api_routes()
        
        # Assign coordination tools to this agent
        for tool in self.tool_registry.get_tools_by_category("coordination"):
            self.add_tool(tool)

    async def initialize_infrastructure(self):
        """Initialize infrastructure connections."""
        try:
            self.vault_client = get_vault_client()
            self.db_client = get_db_client()
            self.openai_client = get_openai_client()
            
            # Configure LLM from Vault
            if self.vault_client:
                # Get agent-specific config
                agent_config = get_agent_config("meta")
                
                # Get OpenAI API key from the correct location
                openai_secret = self.vault_client.get_secret("openai/api_key")
                openai_api_key = None
                if openai_secret and "api_key" in openai_secret:
                    openai_api_key = openai_secret["api_key"]
                
                if openai_api_key:
                    # Configure AutoGen LLM config
                    self.config.llm_config = {
                        "config_list": [{
                            "api_type": "openai",
                            "model": "gpt-4o-mini",
                            "api_key": openai_api_key
                        }],
                        "temperature": 0.7
                    }
                    logger.info("LLM configured with Vault API key")
                else:
                    logger.warning("OpenAI API key not found in Vault")
            
            # Setup API routes
            self._setup_api_routes()
            
            # Start servers (WebSocket and FastAPI)
            self._start_servers()
            
            # Start periodic websocket cleanup task
            asyncio.create_task(self._periodic_websocket_cleanup())
            
            logger.info("Infrastructure initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize infrastructure: {e}")

    async def _periodic_websocket_cleanup(self):
        """Periodically clean up stale websocket connections."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds for more aggressive cleanup
                await self._cleanup_stale_websocket_connections()
                
                # Log current websocket status
                if self.websocket_clients:
                    logger.info(f"Active websocket connections: {len(self.websocket_clients)}")
                    
            except Exception as e:
                logger.error(f"Error in periodic websocket cleanup: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def create_intelligent_task(self, name: str, description: str, 
                                    priority: TaskPriority = TaskPriority.MEDIUM,
                                    required_agents: List[str] = None,
                                    dependencies: List[str] = None) -> str:
        """Create an intelligent task with autonomous assignment."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            description=description,
            priority=priority,
            dependencies=dependencies or []
        )
        
        # Intelligent agent assignment based on capabilities and load
        if required_agents:
            task.assigned_agents = required_agents
        else:
            task.assigned_agents = await self._intelligently_assign_agents(task)
        
        self.tasks[task_id] = task
        await self._add_to_task_queue(task_id)
        logger.info(f"Created intelligent task: {name} (ID: {task_id})")
        return task_id

    async def _intelligently_assign_agents(self, task: Task) -> List[str]:
        """Intelligently assign agents based on capabilities, load, and performance."""
        # Analyze task requirements
        task_keywords = self._extract_task_keywords(task.description)
        
        # Get agent capabilities and current loads
        agent_capabilities = await self._get_agent_capabilities()
        agent_loads = self._get_current_agent_loads()
        
        # Score agents based on capabilities, load, and performance
        agent_scores = {}
        for agent_name, capabilities in agent_capabilities.items():
            capability_score = self._calculate_capability_match(task_keywords, capabilities)
            load_score = self._calculate_load_score(agent_loads.get(agent_name, 0))
            performance_score = self._get_agent_performance_score(agent_name)
            
            # Weighted scoring
            total_score = (capability_score * 0.5 + 
                          load_score * 0.3 + 
                          performance_score * 0.2)
            
            agent_scores[agent_name] = total_score
        
        # Select top agents based on score
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        selected_agents = [agent for agent, score in sorted_agents[:3] if score > 0.5]
        
        return selected_agents

    def _extract_task_keywords(self, description: str) -> List[str]:
        """Extract relevant keywords from task description."""
        # Simple keyword extraction - could be enhanced with NLP
        keywords = []
        description_lower = description.lower()
        
        # Research-related keywords
        if any(word in description_lower for word in ['research', 'analysis', 'data', 'market']):
            keywords.extend(['research', 'analysis', 'data_collection'])
        
        # Signal-related keywords
        if any(word in description_lower for word in ['signal', 'technical', 'indicator', 'pattern']):
            keywords.extend(['signal_generation', 'technical_analysis', 'ml_prediction'])
        
        # Execution-related keywords
        if any(word in description_lower for word in ['trade', 'execute', 'order', 'position']):
            keywords.extend(['trade_execution', 'order_management', 'position_tracking'])
        
        # Strategy-related keywords
        if any(word in description_lower for word in ['strategy', 'optimize', 'backtest']):
            keywords.extend(['strategy_development', 'optimization', 'backtesting'])
        
        # Risk-related keywords
        if any(word in description_lower for word in ['risk', 'compliance', 'audit']):
            keywords.extend(['risk_management', 'compliance_checking', 'audit_trail'])
        
        return keywords

    async def _get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get agent capabilities from MCP tool registry."""
        capabilities = {}
        # Define default capabilities for each agent type
        default_capabilities = {
            'research': ['market_research', 'sentiment_analysis', 'data_collection'],
            'signal': ['technical_analysis', 'signal_generation', 'pattern_recognition'],
            'execution': ['trade_execution', 'order_management', 'position_tracking'],
            'strategy': ['strategy_development', 'optimization', 'backtesting'],
            'risk': ['risk_assessment', 'position_sizing', 'portfolio_protection'],
            'compliance': ['audit_trails', 'regulatory_checks', 'kyc_aml'],
            'backtest': ['historical_analysis', 'performance_evaluation', 'strategy_validation'],
            'optimize': ['parameter_optimization', 'performance_tuning', 'strategy_refinement']
        }
        
        # Use default capabilities if tool registry is not available
        for agent_name in default_capabilities.keys():
            try:
                agent_tools = self.tool_registry.get_tools_by_category(agent_name)
                capabilities[agent_name] = [tool.name for tool in agent_tools] if agent_tools else default_capabilities[agent_name]
            except:
                capabilities[agent_name] = default_capabilities[agent_name]
        
        return capabilities

    def _calculate_capability_match(self, task_keywords: List[str], agent_capabilities: List[str]) -> float:
        """Calculate how well an agent's capabilities match task requirements."""
        if not task_keywords or not agent_capabilities:
            return 0.0
        
        matches = sum(1 for keyword in task_keywords 
                     if any(keyword in capability for capability in agent_capabilities))
        return matches / len(task_keywords)

    def _calculate_load_score(self, current_load: int) -> float:
        """Calculate load score (lower load = higher score)."""
        max_load = 10  # Maximum expected load
        return max(0.0, 1.0 - (current_load / max_load))

    def _get_agent_performance_score(self, agent_name: str) -> float:
        """Get agent performance score based on historical metrics."""
        metrics = self.performance_metrics.get(agent_name, {})
        success_rate = metrics.get('success_rate', 0.5)
        avg_response_time = metrics.get('avg_response_time', 5.0)
        
        # Normalize response time (lower is better)
        response_score = max(0.0, 1.0 - (avg_response_time / 10.0))
        
        return (success_rate * 0.7 + response_score * 0.3)

    async def _add_to_task_queue(self, task_id: str):
        """Add task to priority queue."""
        task = self.tasks[task_id]
        
        # Insert based on priority
        insert_index = 0
        for i, queued_task_id in enumerate(self.task_queue):
            queued_task = self.tasks[queued_task_id]
            if task.priority.value < queued_task.priority.value:
                insert_index = i
                break
            elif task.priority.value == queued_task.priority.value:
                # Same priority, insert by creation time
                if task.created_at < queued_task.created_at:
                    insert_index = i
                    break
            insert_index = i + 1
        
        self.task_queue.insert(insert_index, task_id)

    async def execute_task_with_consensus(self, task_id: str) -> Dict[str, Any]:
        """Execute task with agent consensus mechanism."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        try:
            # Get agent consensus on task execution
            consensus = await self._build_agent_consensus(task)
            self.agent_consensus[task_id] = consensus
            
            # Execute based on consensus
            if consensus.confidence > 0.7:
                result = await self._execute_consensus_decision(task, consensus)
                task.status = TaskStatus.COMPLETED
                task.result = result
            else:
                # Low confidence - need human intervention or retry
                task.status = TaskStatus.FAILED
                task.error = f"Low consensus confidence: {consensus.confidence}"
                result = {"error": task.error, "consensus": consensus.__dict__}
            
            task.completed_at = datetime.now()
            await self._update_agent_loads(task)
            await self._update_performance_metrics(task)
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            logger.error(f"Task execution failed: {e}")
            return {"error": str(e)}

    async def _build_agent_consensus(self, task: Task) -> AgentConsensus:
        """Build consensus among assigned agents."""
        # Ensure task has assigned agents
        await self._ensure_task_has_agents(task)
        
        agent_votes = {}
        agent_reasoning = {}
        
        # Collect votes and reasoning from each agent
        for agent_name in task.assigned_agents:
            vote, reasoning = await self._get_agent_vote(agent_name, task)
            agent_votes[agent_name] = vote
            agent_reasoning[agent_name] = reasoning
        
        # Determine consensus decision
        vote_counts = {}
        for vote in agent_votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        # Find majority decision (handle empty case)
        if vote_counts:
            majority_vote = max(vote_counts.items(), key=lambda x: x[1])[0]
            confidence = vote_counts[majority_vote] / len(agent_votes)
        else:
            majority_vote = "approve"  # Default decision
            confidence = 0.5  # Default confidence
        
        # Aggregate reasoning
        aggregated_reasoning = self._aggregate_reasoning(agent_reasoning)
        
        return AgentConsensus(
            task_id=task.id,
            agents=task.assigned_agents,
            decision=majority_vote,
            confidence=confidence,
            reasoning=aggregated_reasoning,
            votes=agent_votes
        )

    async def _get_agent_vote(self, agent_name: str, task: Task) -> Tuple[str, str]:
        """Get vote and reasoning from a specific agent."""
        # Mock agent voting - in real implementation, this would call the agent
        votes = ["approve", "reject", "modify"]
        reasonings = [
            f"Agent {agent_name} approves task '{task.name}' based on current market conditions",
            f"Agent {agent_name} rejects task '{task.name}' due to risk concerns",
            f"Agent {agent_name} suggests modifications to task '{task.name}' for better execution"
        ]
        
        # Simulate agent decision based on task type and agent role
        if "research" in agent_name and "analysis" in task.description.lower():
            return "approve", reasonings[0]
        elif "risk" in agent_name and "high" in task.description.lower():
            return "reject", reasonings[1]
        else:
            return "modify", reasonings[2]

    async def _ensure_task_has_agents(self, task: Task):
        """Ensure task has assigned agents, assign defaults if needed."""
        if not task.assigned_agents:
            # Assign default agents based on task type
            if "research" in task.description.lower():
                task.assigned_agents = ["research", "signal"]
            elif "signal" in task.description.lower():
                task.assigned_agents = ["signal", "execution"]
            elif "execution" in task.description.lower():
                task.assigned_agents = ["execution", "risk"]
            elif "consensus" in task.description.lower():
                task.assigned_agents = ["research", "signal", "execution"]
            else:
                task.assigned_agents = ["research", "signal", "execution"]

    def _aggregate_reasoning(self, agent_reasoning: Dict[str, str]) -> str:
        """Aggregate reasoning from multiple agents."""
        if not agent_reasoning:
            return "No agent reasoning available"
        
        reasoning_list = list(agent_reasoning.values())
        if len(reasoning_list) == 1:
            return reasoning_list[0]
        
        # Simple aggregation - could be enhanced with NLP
        return f"Consensus reasoning: {'; '.join(reasoning_list)}"

    async def _execute_consensus_decision(self, task: Task, consensus: AgentConsensus) -> Dict[str, Any]:
        """Execute the consensus decision."""
        if consensus.decision == "approve":
            return await self._execute_task(task)
        elif consensus.decision == "reject":
            return {"status": "rejected", "reason": consensus.reasoning}
        elif consensus.decision == "modify":
            return await self._execute_modified_task(task, consensus)
        else:
            raise ValueError(f"Unknown consensus decision: {consensus.decision}")

    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute the task with assigned agents."""
        # Mock task execution - in real implementation, this would coordinate with agents
        execution_results = {}
        
        for agent_name in task.assigned_agents:
            # Simulate agent execution
            result = {
                "agent": agent_name,
                "status": "completed",
                "result": f"Successfully executed {task.name}",
                "timestamp": datetime.now().isoformat()
            }
            execution_results[agent_name] = result
        
        return {
            "task_id": task.id,
            "status": "completed",
            "execution_results": execution_results,
            "completed_at": datetime.now().isoformat()
        }

    async def _execute_modified_task(self, task: Task, consensus: AgentConsensus) -> Dict[str, Any]:
        """Execute task with modifications based on consensus."""
        # Apply modifications based on agent feedback
        modified_task = Task(
            id=f"{task.id}_modified",
            name=f"{task.name} (Modified)",
            description=f"{task.description} - Modified based on agent consensus",
            priority=task.priority,
            assigned_agents=task.assigned_agents
        )
        
        return await self._execute_task(modified_task)

    async def _update_agent_loads(self, task: Task):
        """Update agent load tracking."""
        for agent_name in task.assigned_agents:
            current_load = self.agent_loads.get(agent_name, 0)
            if task.status == TaskStatus.IN_PROGRESS:
                self.agent_loads[agent_name] = current_load + 1
            elif task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                self.agent_loads[agent_name] = max(0, current_load - 1)

    async def _update_performance_metrics(self, task: Task):
        """Update performance metrics for involved agents."""
        for agent_name in task.assigned_agents:
            if agent_name not in self.performance_metrics:
                self.performance_metrics[agent_name] = {
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "avg_response_time": 0.0
                }
            
            metrics = self.performance_metrics[agent_name]
            metrics["total_tasks"] += 1
            
            if task.status == TaskStatus.COMPLETED:
                metrics["successful_tasks"] += 1
            
            # Update average response time
            if task.started_at and task.completed_at:
                response_time = (task.completed_at - task.started_at).total_seconds()
                current_avg = metrics["avg_response_time"]
                total_tasks = metrics["total_tasks"]
                metrics["avg_response_time"] = ((current_avg * (total_tasks - 1)) + response_time) / total_tasks

    def _get_current_agent_loads(self) -> Dict[str, int]:
        """Get current agent loads."""
        return self.agent_loads.copy()

    async def resolve_agent_conflicts(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between agents using intelligent reasoning."""
        conflict_id = str(uuid.uuid4())
        conflict_record = {
            "id": conflict_id,
            "timestamp": datetime.now().isoformat(),
            "conflict_data": conflict_data,
            "resolution": None
        }
        
        try:
            # Analyze conflict type
            conflict_type = self._analyze_conflict_type(conflict_data)
            
            # Apply appropriate resolution strategy
            if conflict_type == "resource":
                resolution = await self._resolve_resource_conflict(conflict_data)
            elif conflict_type == "decision":
                resolution = await self._resolve_decision_conflict(conflict_data)
            elif conflict_type == "priority":
                resolution = await self._resolve_priority_conflict(conflict_data)
            else:
                resolution = await self._resolve_generic_conflict(conflict_data)
            
            conflict_record["resolution"] = resolution
            self.conflict_resolution_history.append(conflict_record)
            
            logger.info(f"Resolved conflict {conflict_id}: {resolution['strategy']}")
            return resolution
            
        except Exception as e:
            error_resolution = {
                "strategy": "error",
                "message": str(e),
                "fallback_action": "manual_intervention"
            }
            conflict_record["resolution"] = error_resolution
            self.conflict_resolution_history.append(conflict_record)
            
            logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return error_resolution

    def _analyze_conflict_type(self, conflict_data: Dict[str, Any]) -> str:
        """Analyze the type of conflict."""
        if "resource" in conflict_data.get("description", "").lower():
            return "resource"
        elif "decision" in conflict_data.get("description", "").lower():
            return "decision"
        elif "priority" in conflict_data.get("description", "").lower():
            return "priority"
        else:
            return "generic"

    async def _resolve_resource_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve resource allocation conflicts."""
        return {
            "strategy": "load_balancing",
            "action": "redistribute_resources",
            "priority_adjustment": "fair_distribution",
            "estimated_resolution_time": "5_minutes"
        }

    async def _resolve_decision_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve decision-making conflicts."""
        return {
            "strategy": "consensus_building",
            "action": "facilitate_discussion",
            "decision_mechanism": "weighted_voting",
            "estimated_resolution_time": "10_minutes"
        }

    async def _resolve_priority_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve priority conflicts."""
        return {
            "strategy": "priority_reassessment",
            "action": "reorder_task_queue",
            "priority_criteria": "business_value_and_urgency",
            "estimated_resolution_time": "3_minutes"
        }

    async def _resolve_generic_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve generic conflicts."""
        return {
            "strategy": "mediation",
            "action": "facilitate_communication",
            "resolution_approach": "compromise_and_consensus",
            "estimated_resolution_time": "15_minutes"
        }

    async def get_system_intelligence_report(self) -> Dict[str, Any]:
        """Generate comprehensive system intelligence report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "task_management": {
                "total_tasks": len(self.tasks),
                "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                "active_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
                "completed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                "failed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
            },
            "agent_coordination": {
                "agent_loads": self.agent_loads,
                "performance_metrics": self.performance_metrics,
                "consensus_decisions": len(self.agent_consensus)
            },
            "conflict_resolution": {
                "total_conflicts": len(self.conflict_resolution_history),
                "resolution_success_rate": self._calculate_resolution_success_rate(),
                "average_resolution_time": self._calculate_average_resolution_time()
            },
            "system_health": {
                "overall_health": "excellent",
                "recommendations": self._generate_system_recommendations()
            }
        }

    def _calculate_resolution_success_rate(self) -> float:
        """Calculate conflict resolution success rate."""
        if not self.conflict_resolution_history:
            return 0.0
        
        successful_resolutions = sum(1 for record in self.conflict_resolution_history
                                   if record["resolution"] and record["resolution"]["strategy"] != "error")
        return successful_resolutions / len(self.conflict_resolution_history)

    def _calculate_average_resolution_time(self) -> float:
        """Calculate average conflict resolution time."""
        # Mock calculation - in real implementation, would track actual times
        return 8.5  # minutes

    def _generate_system_recommendations(self) -> List[str]:
        """Generate intelligent system recommendations."""
        recommendations = []
        
        # Analyze task queue
        if len(self.task_queue) > 10:
            recommendations.append("Consider adding more agents to handle high task volume")
        
        # Analyze agent loads
        overloaded_agents = [agent for agent, load in self.agent_loads.items() if load > 5]
        if overloaded_agents:
            recommendations.append(f"Agents {overloaded_agents} are overloaded - consider load balancing")
        
        # Analyze performance
        low_performance_agents = [agent for agent, metrics in self.performance_metrics.items()
                                if metrics.get('success_rate', 1.0) < 0.7]
        if low_performance_agents:
            recommendations.append(f"Agents {low_performance_agents} show low performance - consider optimization")
        
        return recommendations

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed status of a specific task."""
        if task_id not in self.tasks:
            return {"error": f"Task {task_id} not found"}
        
        task = self.tasks[task_id]
        consensus = self.agent_consensus.get(task_id)
        
        return {
            "task_id": task_id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.value,
            "assigned_agents": task.assigned_agents,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error,
            "consensus": consensus.__dict__ if consensus else None
        }

    async def get_agent_intelligence_report(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed intelligence report for a specific agent."""
        metrics = self.performance_metrics.get(agent_name, {})
        current_load = self.agent_loads.get(agent_name, 0)
        
        return {
            "agent_name": agent_name,
            "current_load": current_load,
            "performance_metrics": metrics,
            "capabilities": await self._get_agent_capabilities_for_agent(agent_name),
            "recent_tasks": await self._get_recent_tasks_for_agent(agent_name),
            "recommendations": self._generate_agent_recommendations(agent_name, metrics, current_load)
        }

    async def _get_agent_capabilities_for_agent(self, agent_name: str) -> List[str]:
        """Get capabilities for a specific agent."""
        capabilities = await self._get_agent_capabilities()
        return capabilities.get(agent_name, [])

    async def _get_recent_tasks_for_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get recent tasks for a specific agent."""
        recent_tasks = []
        for task in self.tasks.values():
            if agent_name in task.assigned_agents:
                recent_tasks.append({
                    "task_id": task.id,
                    "name": task.name,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat()
                })
        
        # Return last 5 tasks
        return sorted(recent_tasks, key=lambda x: x["created_at"], reverse=True)[:5]

    def _generate_agent_recommendations(self, agent_name: str, metrics: Dict[str, Any], current_load: int) -> List[str]:
        """Generate recommendations for a specific agent."""
        recommendations = []
        
        if current_load > 5:
            recommendations.append("Consider reducing workload to improve performance")
        
        success_rate = metrics.get('success_rate', 1.0)
        if success_rate < 0.7:
            recommendations.append("Performance below threshold - consider training or optimization")
        
        avg_response_time = metrics.get('avg_response_time', 0.0)
        if avg_response_time > 10.0:
            recommendations.append("Response time is high - consider resource allocation")
        
        return recommendations

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status with autonomous decision making info."""
        try:
            return {
                "agent_type": "agentic_meta",
                "status": "healthy",
                "autonomous_decisions_count": len(self.autonomous_decisions),
                "decision_history_count": len(self.decision_history),
                "validation_success_rate": self._calculate_validation_success_rate(),
                "average_decision_confidence": self._calculate_average_decision_confidence(),
                "recent_decisions": self._get_recent_decisions(5),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {"error": str(e)}

    # ============================================================================
    # PHASE 5.1: AUTONOMOUS DECISION MAKING
    # ============================================================================

    async def make_autonomous_decision(self, decision_type: str, context: Dict[str, Any]) -> AutonomousDecision:
        """Make an autonomous decision with reasoning and validation."""
        try:
            decision_id = str(uuid.uuid4())
            
            # Generate decision using autonomous reasoning
            decision_result = await self._autonomous_reasoning(decision_type, context)
            
            # Create autonomous decision object
            autonomous_decision = AutonomousDecision(
                id=decision_id,
                decision_type=decision_type,
                context=context,
                decision=decision_result["decision"],
                confidence=decision_result["confidence"],
                reasoning=decision_result["reasoning"],
                alternatives=decision_result["alternatives"]
            )
            
            # Store decision
            self.autonomous_decisions[decision_id] = autonomous_decision
            self.decision_history.append(autonomous_decision)
            
            # Validate decision
            await self._validate_decision(autonomous_decision)
            
            # Learn from decision
            await self._learn_from_decision(autonomous_decision)
            
            logger.info(f"Autonomous decision made: {decision_type} (ID: {decision_id})")
            return autonomous_decision
            
        except Exception as e:
            logger.error(f"Error making autonomous decision: {e}")
            raise

    async def _autonomous_reasoning(self, decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform autonomous reasoning to generate decisions."""
        try:
            # Create reasoning prompt based on decision type
            prompt = self._create_reasoning_prompt(decision_type, context)
            
            # Get agent reasoning using LLM
            response = await self._get_agent_response(prompt)
            
            # Parse response into structured decision
            decision_result = {
                "decision": response.get("decision", "default_decision"),
                "confidence": response.get("confidence", 0.5),
                "reasoning": response.get("reasoning", "No reasoning provided"),
                "alternatives": response.get("alternatives", [])
            }
            
            return decision_result
            
        except Exception as e:
            logger.error(f"Error in autonomous reasoning: {e}")
            return {
                "decision": "fallback_decision",
                "confidence": 0.1,
                "reasoning": f"Fallback due to error: {e}",
                "alternatives": []
            }

    def _create_reasoning_prompt(self, decision_type: str, context: Dict[str, Any]) -> str:
        """Create a reasoning prompt for autonomous decision making."""
        base_prompt = f"""
        You are an autonomous decision-making agent for a trading system. 
        You need to make a decision about: {decision_type}
        
        Context: {json.dumps(context, indent=2)}
        
        Please provide:
        1. A clear decision
        2. Your confidence level (0.0 to 1.0)
        3. Detailed reasoning for your decision
        4. Alternative options you considered
        
        Respond in JSON format:
        {{
            "decision": "your_decision",
            "confidence": 0.85,
            "reasoning": "detailed_reasoning",
            "alternatives": ["alt1", "alt2", "alt3"]
        }}
        """
        return base_prompt

    async def _validate_decision(self, decision: AutonomousDecision) -> None:
        """Validate an autonomous decision using multiple methods."""
        try:
            # Multiple validation methods
            validation_methods = [
                self._validate_against_history,
                self._validate_against_rules,
                self._validate_against_consensus
            ]
            
            validation_scores = []
            validation_feedback = []
            
            for method in validation_methods:
                try:
                    score, feedback = await method(decision)
                    validation_scores.append(score)
                    validation_feedback.append(feedback)
                except Exception as e:
                    logger.warning(f"Validation method failed: {e}")
                    validation_scores.append(0.5)  # Neutral score
                    validation_feedback.append(f"Validation failed: {e}")
            
            # Calculate overall validation score
            overall_score = sum(validation_scores) / len(validation_scores)
            
            # Update decision validation status
            decision.validation_score = overall_score
            if overall_score >= 0.7:
                decision.validation_status = "validated"
            elif overall_score >= 0.4:
                decision.validation_status = "needs_review"
            else:
                decision.validation_status = "rejected"
            
            # Store validation results
            validation = DecisionValidation(
                decision_id=decision.id,
                validation_method="multi_method",
                score=overall_score,
                feedback="; ".join(validation_feedback),
                recommendations=self._generate_validation_recommendations(overall_score, validation_feedback)
            )
            
            self.decision_validation[decision.id] = validation
            
            logger.info(f"Decision {decision.id} validated with score: {overall_score}")
            
        except Exception as e:
            logger.error(f"Error validating decision: {e}")

    async def _validate_against_history(self, decision: AutonomousDecision) -> Tuple[float, str]:
        """Validate decision against historical patterns."""
        try:
            # Find similar historical decisions
            similar_decisions = self._find_similar_decisions(decision)
            
            if not similar_decisions:
                return 0.5, "No historical data for comparison"
            
            # Calculate success rate of similar decisions
            success_rate = sum(1 for d in similar_decisions if d.validation_score > 0.7) / len(similar_decisions)
            
            feedback = f"Historical success rate: {success_rate:.2f}"
            return success_rate, feedback
            
        except Exception as e:
            return 0.5, f"History validation error: {e}"

    async def _validate_against_rules(self, decision: AutonomousDecision) -> Tuple[float, str]:
        """Validate decision against predefined rules."""
        try:
            # Define validation rules based on decision type
            rules = self._get_validation_rules(decision.decision_type)
            
            rule_violations = 0
            total_rules = len(rules)
            
            for rule_name, rule_check in rules.items():
                if not rule_check(decision):
                    rule_violations += 1
            
            compliance_rate = (total_rules - rule_violations) / total_rules
            feedback = f"Rule compliance: {compliance_rate:.2f} ({rule_violations} violations)"
            
            return compliance_rate, feedback
            
        except Exception as e:
            return 0.5, f"Rule validation error: {e}"

    async def _validate_against_consensus(self, decision: AutonomousDecision) -> Tuple[float, str]:
        """Validate decision against agent consensus."""
        try:
            # Get consensus from other agents if available
            consensus_agents = ["research", "signal", "strategy", "risk"]
            consensus_votes = []
            
            for agent_name in consensus_agents:
                try:
                    # This would normally query other agents
                    # For now, simulate consensus
                    vote = 0.7  # Simulated consensus score
                    consensus_votes.append(vote)
                except Exception:
                    continue
            
            if consensus_votes:
                consensus_score = sum(consensus_votes) / len(consensus_votes)
                feedback = f"Agent consensus: {consensus_score:.2f}"
                return consensus_score, feedback
            else:
                return 0.5, "No consensus data available"
                
        except Exception as e:
            return 0.5, f"Consensus validation error: {e}"

    def _get_validation_rules(self, decision_type: str) -> Dict[str, callable]:
        """Get validation rules for a specific decision type."""
        rules = {
            "risk_management": {
                "max_risk": lambda d: d.confidence >= 0.8,
                "position_size": lambda d: "position_size" in d.context and d.context["position_size"] <= 0.1
            },
            "strategy_selection": {
                "market_conditions": lambda d: "market_conditions" in d.context,
                "performance_history": lambda d: d.confidence >= 0.7
            },
            "trade_execution": {
                "signal_strength": lambda d: d.confidence >= 0.6,
                "market_volatility": lambda d: "volatility" in d.context
            }
        }
        
        return rules.get(decision_type, {
            "default_rule": lambda d: True
        })

    def _find_similar_decisions(self, decision: AutonomousDecision) -> List[AutonomousDecision]:
        """Find similar historical decisions for validation."""
        similar_decisions = []
        
        for hist_decision in self.decision_history[-100:]:  # Last 100 decisions
            if hist_decision.decision_type == decision.decision_type:
                # Simple similarity check - could be enhanced with ML
                similar_decisions.append(hist_decision)
        
        return similar_decisions

    def _generate_validation_recommendations(self, score: float, feedback: List[str]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if score < 0.4:
            recommendations.append("Consider alternative approaches")
            recommendations.append("Gather more context before deciding")
        elif score < 0.7:
            recommendations.append("Review decision with additional validation")
            recommendations.append("Monitor decision outcomes closely")
        else:
            recommendations.append("Decision appears sound")
            recommendations.append("Proceed with confidence")
        
        return recommendations

    async def _learn_from_decision(self, decision: AutonomousDecision) -> None:
        """Learn from decision outcomes and improve future decisions."""
        try:
            # Store learning data
            learning_data = {
                "decision_id": decision.id,
                "decision_type": decision.decision_type,
                "context": decision.context,
                "confidence": decision.confidence,
                "validation_score": decision.validation_score,
                "timestamp": decision.timestamp
            }
            
            self.decision_learning[decision.id] = learning_data
            
            # Update learning patterns
            await self._update_learning_patterns(decision)
            
            logger.info(f"Learning data stored for decision {decision.id}")
            
        except Exception as e:
            logger.error(f"Error learning from decision: {e}")

    async def _update_learning_patterns(self, decision: AutonomousDecision) -> None:
        """Update learning patterns based on decision outcomes."""
        try:
            # Analyze decision patterns
            pattern_key = f"{decision.decision_type}_{decision.validation_score:.1f}"
            
            if pattern_key not in self.decision_learning:
                self.decision_learning[pattern_key] = {
                    "count": 0,
                    "total_confidence": 0,
                    "total_validation_score": 0,
                    "success_rate": 0
                }
            
            pattern = self.decision_learning[pattern_key]
            pattern["count"] += 1
            pattern["total_confidence"] += decision.confidence
            pattern["total_validation_score"] += decision.validation_score
            
            # Calculate success rate
            if decision.validation_score >= 0.7:
                pattern["success_rate"] = (pattern["success_rate"] * (pattern["count"] - 1) + 1) / pattern["count"]
            else:
                pattern["success_rate"] = (pattern["success_rate"] * (pattern["count"] - 1)) / pattern["count"]
            
            logger.debug(f"Updated learning pattern: {pattern_key}")
            
        except Exception as e:
            logger.error(f"Error updating learning patterns: {e}")

    def _calculate_validation_success_rate(self) -> float:
        """Calculate the success rate of decision validation."""
        if not self.decision_history:
            return 0.0
        
        successful_decisions = sum(1 for d in self.decision_history if d.validation_score >= 0.7)
        return successful_decisions / len(self.decision_history)

    def _calculate_average_decision_confidence(self) -> float:
        """Calculate the average confidence of recent decisions."""
        if not self.decision_history:
            return 0.0
        
        recent_decisions = self.decision_history[-10:]  # Last 10 decisions
        return sum(d.confidence for d in recent_decisions) / len(recent_decisions)

    def _get_recent_decisions(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent autonomous decisions."""
        recent = self.decision_history[-count:]
        return [
            {
                "id": d.id,
                "type": d.decision_type,
                "decision": d.decision,
                "confidence": d.confidence,
                "validation_score": d.validation_score,
                "timestamp": d.timestamp.isoformat()
            }
            for d in recent
        ]

    async def explain_decision(self, decision_id: str) -> Dict[str, Any]:
        """Provide detailed explanation of an autonomous decision."""
        try:
            if decision_id not in self.autonomous_decisions:
                return {"error": "Decision not found"}
            
            decision = self.autonomous_decisions[decision_id]
            validation = self.decision_validation.get(decision_id)
            
            explanation = {
                "decision_id": decision_id,
                "decision_type": decision.decision_type,
                "decision": decision.decision,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "alternatives": decision.alternatives,
                "context": decision.context,
                "validation": {
                    "status": decision.validation_status,
                    "score": decision.validation_score,
                    "feedback": validation.feedback if validation else "No validation data",
                    "recommendations": validation.recommendations if validation else []
                },
                "learning_feedback": decision.learning_feedback,
                "timestamp": decision.timestamp.isoformat()
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining decision: {e}")
            return {"error": str(e)}

    async def _get_agent_response(self, prompt: str) -> Dict[str, Any]:
        """Get response from the agent's LLM for autonomous reasoning."""
        try:
            # Use the agent's LLM to generate a response
            if hasattr(self, 'agent') and self.agent:
                # Use AutoGen agent's LLM
                response = await self.agent.a_generate_response(prompt)
                # Parse JSON response
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # Fallback if response is not valid JSON
                    return {
                        "decision": "default_decision",
                        "confidence": 0.5,
                        "reasoning": response,
                        "alternatives": []
                    }
            else:
                # Fallback response
                return {
                    "decision": "fallback_decision",
                    "confidence": 0.5,
                    "reasoning": "No LLM available for reasoning",
                    "alternatives": []
                }
                
        except Exception as e:
            logger.error(f"Error getting agent response: {e}")
            return {
                "decision": "error_decision",
                "confidence": 0.1,
                "reasoning": f"Error in reasoning: {e}",
                "alternatives": []
            } 

    # ============================================================================
    # PHASE 5.2: AGENT SELF-DIRECTION
    # ============================================================================

    async def set_agent_goal(self, agent_name: str, goal_type: str, goal_params: Dict[str, Any]) -> Dict[str, Any]:
        """Set a goal for a specific agent with self-direction capabilities."""
        try:
            goal_id = str(uuid.uuid4())
            
            goal = {
                "id": goal_id,
                "agent_name": agent_name,
                "goal_type": goal_type,
                "goal_params": goal_params,
                "status": "active",
                "created_at": datetime.now(),
                "progress": 0.0,
                "target_metrics": goal_params.get("target_metrics", {}),
                "deadline": goal_params.get("deadline"),
                "priority": goal_params.get("priority", "medium")
            }
            
            self.agent_goals[goal_id] = goal
            
            # Initialize monitoring for this goal
            await self._initialize_goal_monitoring(goal)
            
            logger.info(f"Goal set for {agent_name}: {goal_type} (ID: {goal_id})")
            return {"goal_id": goal_id, "status": "created"}
            
        except Exception as e:
            logger.error(f"Error setting agent goal: {e}")
            return {"error": str(e)}

    async def _initialize_goal_monitoring(self, goal: Dict[str, Any]) -> None:
        """Initialize monitoring for a specific goal."""
        try:
            agent_name = goal["agent_name"]
            
            # Set up baseline metrics
            baseline_metrics = await self._get_agent_baseline_metrics(agent_name)
            
            self.self_monitoring_data[goal["id"]] = {
                "baseline_metrics": baseline_metrics,
                "current_metrics": baseline_metrics,
                "progress_history": [],
                "optimization_attempts": [],
                "learning_insights": []
            }
            
            logger.debug(f"Goal monitoring initialized for {goal['id']}")
            
        except Exception as e:
            logger.error(f"Error initializing goal monitoring: {e}")

    async def _get_agent_baseline_metrics(self, agent_name: str) -> Dict[str, Any]:
        """Get baseline performance metrics for an agent."""
        try:
            # Get current agent performance
            agent_status = await self.get_agent_intelligence_report(agent_name)
            
            baseline_metrics = {
                "response_time": agent_status.get("average_response_time", 1.0),
                "success_rate": agent_status.get("success_rate", 0.5),
                "task_completion_rate": agent_status.get("task_completion_rate", 0.5),
                "error_rate": agent_status.get("error_rate", 0.1),
                "resource_usage": agent_status.get("resource_usage", {}),
                "timestamp": datetime.now()
            }
            
            return baseline_metrics
            
        except Exception as e:
            logger.error(f"Error getting baseline metrics: {e}")
            return {
                "response_time": 1.0,
                "success_rate": 0.5,
                "task_completion_rate": 0.5,
                "error_rate": 0.1,
                "resource_usage": {},
                "timestamp": datetime.now()
            }

    async def monitor_agent_self_performance(self, agent_name: str) -> Dict[str, Any]:
        """Monitor agent's self-performance and identify improvement opportunities."""
        try:
            # Get current performance metrics
            current_metrics = await self._get_agent_current_metrics(agent_name)
            
            # Analyze performance trends
            performance_analysis = await self._analyze_performance_trends(agent_name, current_metrics)
            
            # Identify optimization opportunities
            optimization_opportunities = await self._identify_optimization_opportunities(agent_name, current_metrics)
            
            # Generate self-improvement recommendations
            recommendations = await self._generate_self_improvement_recommendations(agent_name, performance_analysis)
            
            monitoring_report = {
                "agent_name": agent_name,
                "current_metrics": current_metrics,
                "performance_analysis": performance_analysis,
                "optimization_opportunities": optimization_opportunities,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store monitoring data
            self.self_monitoring_data[agent_name] = monitoring_report
            
            logger.info(f"Self-performance monitoring completed for {agent_name}")
            return monitoring_report
            
        except Exception as e:
            logger.error(f"Error monitoring agent self-performance: {e}")
            return {"error": str(e)}

    async def _get_agent_current_metrics(self, agent_name: str) -> Dict[str, Any]:
        """Get current performance metrics for an agent."""
        try:
            # Get agent status and performance data
            agent_status = await self.get_agent_intelligence_report(agent_name)
            
            current_metrics = {
                "response_time": agent_status.get("average_response_time", 1.0),
                "success_rate": agent_status.get("success_rate", 0.5),
                "task_completion_rate": agent_status.get("task_completion_rate", 0.5),
                "error_rate": agent_status.get("error_rate", 0.1),
                "resource_usage": agent_status.get("resource_usage", {}),
                "decision_confidence": agent_status.get("average_decision_confidence", 0.5),
                "timestamp": datetime.now()
            }
            
            return current_metrics
            
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return {}

    async def _analyze_performance_trends(self, agent_name: str, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends for an agent."""
        try:
            # Get historical performance data
            historical_data = self.performance_metrics.get(agent_name, [])
            
            if not historical_data:
                return {"trend": "no_data", "change_rate": 0.0}
            
            # Calculate trends
            recent_metrics = historical_data[-5:]  # Last 5 data points
            
            # Calculate change rates
            response_time_change = self._calculate_change_rate([m.get("response_time", 1.0) for m in recent_metrics])
            success_rate_change = self._calculate_change_rate([m.get("success_rate", 0.5) for m in recent_metrics])
            
            trend_analysis = {
                "response_time_trend": "improving" if response_time_change < 0 else "declining",
                "success_rate_trend": "improving" if success_rate_change > 0 else "declining",
                "overall_trend": "improving" if success_rate_change > 0 and response_time_change < 0 else "declining",
                "change_rates": {
                    "response_time": response_time_change,
                    "success_rate": success_rate_change
                }
            }
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {"trend": "error", "change_rate": 0.0}

    def _calculate_change_rate(self, values: List[float]) -> float:
        """Calculate the rate of change for a list of values."""
        if len(values) < 2:
            return 0.0
        
        # Calculate average change rate
        changes = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                change = (values[i] - values[i-1]) / values[i-1]
                changes.append(change)
        
        return sum(changes) / len(changes) if changes else 0.0

    async def _identify_optimization_opportunities(self, agent_name: str, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities for an agent."""
        opportunities = []
        
        try:
            # Check response time optimization
            if current_metrics.get("response_time", 1.0) > 0.5:
                opportunities.append({
                    "type": "response_time_optimization",
                    "priority": "high",
                    "description": "Response time is above optimal threshold",
                    "potential_improvement": "20-30% reduction in response time",
                    "recommended_actions": ["Optimize algorithm efficiency", "Implement caching", "Reduce API calls"]
                })
            
            # Check success rate optimization
            if current_metrics.get("success_rate", 0.5) < 0.8:
                opportunities.append({
                    "type": "success_rate_optimization",
                    "priority": "high",
                    "description": "Success rate is below target threshold",
                    "potential_improvement": "10-20% increase in success rate",
                    "recommended_actions": ["Improve error handling", "Enhance decision logic", "Add validation checks"]
                })
            
            # Check error rate optimization
            if current_metrics.get("error_rate", 0.1) > 0.05:
                opportunities.append({
                    "type": "error_rate_optimization",
                    "priority": "medium",
                    "description": "Error rate is above acceptable threshold",
                    "potential_improvement": "50% reduction in error rate",
                    "recommended_actions": ["Improve error handling", "Add retry mechanisms", "Enhance logging"]
                })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying optimization opportunities: {e}")
            return []

    async def _generate_self_improvement_recommendations(self, agent_name: str, performance_analysis: Dict[str, Any]) -> List[str]:
        """Generate self-improvement recommendations for an agent."""
        recommendations = []
        
        try:
            trend = performance_analysis.get("overall_trend", "stable")
            
            if trend == "declining":
                recommendations.append("Implement performance monitoring and alerting")
                recommendations.append("Review and optimize core algorithms")
                recommendations.append("Add caching mechanisms for frequently accessed data")
                recommendations.append("Implement retry logic for failed operations")
            
            elif trend == "improving":
                recommendations.append("Continue current optimization strategies")
                recommendations.append("Monitor for potential over-optimization")
                recommendations.append("Document successful optimization techniques")
            
            else:
                recommendations.append("Establish baseline performance metrics")
                recommendations.append("Implement continuous monitoring")
                recommendations.append("Set up performance improvement goals")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating self-improvement recommendations: {e}")
            return ["Error generating recommendations"]

    async def optimize_agent_self_performance(self, agent_name: str, optimization_type: str = "auto") -> Dict[str, Any]:
        """Optimize agent's self-performance based on monitoring data."""
        try:
            # Get current monitoring data
            monitoring_data = self.self_monitoring_data.get(agent_name, {})
            
            if not monitoring_data:
                return {"error": "No monitoring data available"}
            
            # Determine optimization strategy
            optimization_strategy = await self._determine_optimization_strategy(agent_name, monitoring_data, optimization_type)
            
            # Apply optimization
            optimization_result = await self._apply_optimization(agent_name, optimization_strategy)
            
            # Track optimization attempt
            optimization_record = {
                "agent_name": agent_name,
                "optimization_type": optimization_type,
                "strategy": optimization_strategy,
                "result": optimization_result,
                "timestamp": datetime.now()
            }
            
            self.optimization_history.append(optimization_record)
            
            logger.info(f"Self-optimization completed for {agent_name}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing agent self-performance: {e}")
            return {"error": str(e)}

    async def _determine_optimization_strategy(self, agent_name: str, monitoring_data: Dict[str, Any], optimization_type: str) -> Dict[str, Any]:
        """Determine the best optimization strategy for an agent."""
        try:
            current_metrics = monitoring_data.get("current_metrics", {})
            opportunities = monitoring_data.get("optimization_opportunities", [])
            
            if optimization_type == "auto":
                # Automatically determine best strategy
                if opportunities:
                    # Prioritize by priority level
                    high_priority = [opp for opp in opportunities if opp.get("priority") == "high"]
                    if high_priority:
                        return {
                            "type": "targeted_optimization",
                            "target": high_priority[0]["type"],
                            "actions": high_priority[0]["recommended_actions"]
                        }
                
                # Default strategy
                return {
                    "type": "general_optimization",
                    "target": "overall_performance",
                    "actions": ["Implement caching", "Optimize algorithms", "Add error handling"]
                }
            
            else:
                # Manual optimization strategy
                return {
                    "type": "manual_optimization",
                    "target": optimization_type,
                    "actions": ["Manual optimization applied"]
                }
                
        except Exception as e:
            logger.error(f"Error determining optimization strategy: {e}")
            return {"type": "fallback", "target": "general", "actions": []}

    async def _apply_optimization(self, agent_name: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optimization strategy to an agent."""
        try:
            optimization_type = strategy.get("type", "general")
            target = strategy.get("target", "overall_performance")
            actions = strategy.get("actions", [])
            
            # Apply optimization actions (simulated for now)
            applied_actions = []
            for action in actions:
                # In a real implementation, these would be actual optimizations
                applied_actions.append({
                    "action": action,
                    "status": "applied",
                    "impact": "simulated_improvement"
                })
            
            optimization_result = {
                "agent_name": agent_name,
                "optimization_type": optimization_type,
                "target": target,
                "applied_actions": applied_actions,
                "estimated_improvement": "10-20% performance improvement",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return {"error": str(e)}

    async def learn_from_self_experience(self, agent_name: str) -> Dict[str, Any]:
        """Enable agent to learn from its own experience and improve over time."""
        try:
            # Get learning data
            learning_data = await self._collect_learning_data(agent_name)
            
            # Analyze learning patterns
            learning_patterns = await self._analyze_learning_patterns(agent_name, learning_data)
            
            # Generate learning insights
            learning_insights = await self._generate_learning_insights(agent_name, learning_patterns)
            
            # Apply learning improvements
            improvements = await self._apply_learning_improvements(agent_name, learning_insights)
            
            # Update learning progress
            self.learning_progress[agent_name] = {
                "learning_data": learning_data,
                "patterns": learning_patterns,
                "insights": learning_insights,
                "improvements": improvements,
                "last_updated": datetime.now()
            }
            
            learning_report = {
                "agent_name": agent_name,
                "learning_patterns": learning_patterns,
                "insights": learning_insights,
                "improvements": improvements,
                "progress_score": self._calculate_learning_progress(agent_name),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Self-learning completed for {agent_name}")
            return learning_report
            
        except Exception as e:
            logger.error(f"Error in self-learning: {e}")
            return {"error": str(e)}

    async def _collect_learning_data(self, agent_name: str) -> Dict[str, Any]:
        """Collect learning data for an agent."""
        try:
            # Collect various types of learning data
            decision_data = self.decision_history[-50:]  # Last 50 decisions
            performance_data = self.performance_metrics.get(agent_name, [])
            optimization_data = [opt for opt in self.optimization_history if opt.get("agent_name") == agent_name]
            
            learning_data = {
                "decisions": decision_data,
                "performance": performance_data,
                "optimizations": optimization_data,
                "monitoring_data": self.self_monitoring_data.get(agent_name, {}),
                "timestamp": datetime.now()
            }
            
            return learning_data
            
        except Exception as e:
            logger.error(f"Error collecting learning data: {e}")
            return {}

    async def _analyze_learning_patterns(self, agent_name: str, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze learning patterns from collected data."""
        try:
            decisions = learning_data.get("decisions", [])
            performance = learning_data.get("performance", [])
            
            patterns = {
                "decision_patterns": self._analyze_decision_patterns(decisions),
                "performance_patterns": self._analyze_performance_patterns(performance),
                "improvement_patterns": self._analyze_improvement_patterns(learning_data)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {e}")
            return {}

    def _analyze_decision_patterns(self, decisions: List[AutonomousDecision]) -> Dict[str, Any]:
        """Analyze patterns in decision making."""
        if not decisions:
            return {"pattern": "no_data"}
        
        # Analyze decision confidence trends
        confidences = [d.confidence for d in decisions]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Analyze decision types
        decision_types = {}
        for decision in decisions:
            decision_type = decision.decision_type
            decision_types[decision_type] = decision_types.get(decision_type, 0) + 1
        
        return {
            "average_confidence": avg_confidence,
            "confidence_trend": "improving" if confidences[-1] > confidences[0] else "declining",
            "decision_type_distribution": decision_types,
            "total_decisions": len(decisions)
        }

    def _analyze_performance_patterns(self, performance: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in performance data."""
        if not performance:
            return {"pattern": "no_data"}
        
        # Analyze success rate trends
        success_rates = [p.get("success_rate", 0.5) for p in performance]
        avg_success_rate = sum(success_rates) / len(success_rates)
        
        return {
            "average_success_rate": avg_success_rate,
            "success_rate_trend": "improving" if success_rates[-1] > success_rates[0] else "declining",
            "performance_stability": "stable" if max(success_rates) - min(success_rates) < 0.2 else "volatile"
        }

    def _analyze_improvement_patterns(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in improvement attempts."""
        optimizations = learning_data.get("optimizations", [])
        
        if not optimizations:
            return {"pattern": "no_optimizations"}
        
        # Analyze optimization frequency and success
        optimization_types = {}
        for opt in optimizations:
            opt_type = opt.get("optimization_type", "unknown")
            optimization_types[opt_type] = optimization_types.get(opt_type, 0) + 1
        
        return {
            "total_optimizations": len(optimizations),
            "optimization_types": optimization_types,
            "optimization_frequency": "high" if len(optimizations) > 5 else "low"
        }

    async def _generate_learning_insights(self, agent_name: str, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights from learning patterns."""
        insights = []
        
        try:
            decision_patterns = patterns.get("decision_patterns", {})
            performance_patterns = patterns.get("performance_patterns", {})
            
            # Generate insights based on patterns
            if decision_patterns.get("confidence_trend") == "declining":
                insights.append("Decision confidence is declining - consider reviewing decision logic")
            
            if performance_patterns.get("success_rate_trend") == "declining":
                insights.append("Success rate is declining - focus on error handling and validation")
            
            if performance_patterns.get("performance_stability") == "volatile":
                insights.append("Performance is volatile - implement more consistent algorithms")
            
            # Add general insights
            insights.append("Continue monitoring and learning from outcomes")
            insights.append("Regular optimization helps maintain performance")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")
            return ["Error generating insights"]

    async def _apply_learning_improvements(self, agent_name: str, insights: List[str]) -> List[Dict[str, Any]]:
        """Apply improvements based on learning insights."""
        improvements = []
        
        try:
            for insight in insights:
                improvement = {
                    "insight": insight,
                    "action": self._determine_improvement_action(insight),
                    "status": "applied",
                    "timestamp": datetime.now()
                }
                improvements.append(improvement)
            
            return improvements
            
        except Exception as e:
            logger.error(f"Error applying learning improvements: {e}")
            return []

    def _determine_improvement_action(self, insight: str) -> str:
        """Determine appropriate action based on insight."""
        if "confidence" in insight.lower():
            return "Review and enhance decision-making algorithms"
        elif "success rate" in insight.lower():
            return "Improve error handling and validation processes"
        elif "volatile" in insight.lower():
            return "Implement more consistent and stable algorithms"
        else:
            return "Continue monitoring and optimization"

    def _calculate_learning_progress(self, agent_name: str) -> float:
        """Calculate learning progress score for an agent."""
        try:
            progress_data = self.learning_progress.get(agent_name, {})
            
            if not progress_data:
                return 0.0
            
            # Calculate progress based on various factors
            insights_count = len(progress_data.get("insights", []))
            improvements_count = len(progress_data.get("improvements", []))
            
            # Simple progress calculation
            progress_score = min(1.0, (insights_count * 0.1 + improvements_count * 0.05))
            
            return progress_score
            
        except Exception as e:
            logger.error(f"Error calculating learning progress: {e}")
            return 0.0 

    # ============================================================================
    # PHASE 5.3: CREATIVE PROBLEM SOLVING
    # ============================================================================

    async def solve_problem_creatively(self, problem_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Solve a problem using creative reasoning and innovative approaches."""
        try:
            solution_id = str(uuid.uuid4())
            
            # Perform creative reasoning
            creative_analysis = await self._creative_reasoning(problem_description, context)
            
            # Generate innovative solutions
            innovative_solutions = await self._generate_innovative_solutions(problem_description, creative_analysis)
            
            # Develop adaptive strategies
            adaptive_strategies = await self._develop_adaptive_strategies(problem_description, innovative_solutions)
            
            # Create novel approaches
            novel_approaches = await self._create_novel_approaches(problem_description, adaptive_strategies)
            
            # Select best creative solution
            best_solution = await self._select_best_creative_solution(innovative_solutions, adaptive_strategies, novel_approaches)
            
            # Store creative solution
            creative_solution = {
                "id": solution_id,
                "problem_description": problem_description,
                "context": context,
                "creative_analysis": creative_analysis,
                "innovative_solutions": innovative_solutions,
                "adaptive_strategies": adaptive_strategies,
                "novel_approaches": novel_approaches,
                "selected_solution": best_solution,
                "creativity_score": best_solution.get("creativity_score", 0.0),
                "innovation_level": best_solution.get("innovation_level", "moderate"),
                "timestamp": datetime.now()
            }
            
            self.creative_solutions[solution_id] = creative_solution
            self.innovation_history.append(creative_solution)
            
            # Learn from creative solution
            await self._learn_from_creative_solution(creative_solution)
            
            logger.info(f"Creative problem solving completed: {problem_description[:50]}... (ID: {solution_id})")
            return creative_solution
            
        except Exception as e:
            logger.error(f"Error in creative problem solving: {e}")
            return {"error": str(e)}

    async def _creative_reasoning(self, problem_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform creative reasoning to understand and analyze problems."""
        try:
            # Create creative reasoning prompt
            prompt = self._create_creative_reasoning_prompt(problem_description, context)
            
            # Get creative analysis from LLM
            response = await self._get_agent_response(prompt)
            
            # Parse creative analysis
            creative_analysis = {
                "problem_breakdown": response.get("problem_breakdown", []),
                "root_causes": response.get("root_causes", []),
                "constraints": response.get("constraints", []),
                "opportunities": response.get("opportunities", []),
                "creative_insights": response.get("creative_insights", []),
                "unconventional_angles": response.get("unconventional_angles", [])
            }
            
            return creative_analysis
            
        except Exception as e:
            logger.error(f"Error in creative reasoning: {e}")
            return {
                "problem_breakdown": ["Error in creative reasoning"],
                "root_causes": [],
                "constraints": [],
                "opportunities": [],
                "creative_insights": [],
                "unconventional_angles": []
            }

    def _create_creative_reasoning_prompt(self, problem_description: str, context: Dict[str, Any]) -> str:
        """Create a prompt for creative reasoning."""
        prompt = f"""
        You are a creative problem-solving agent. Analyze this problem from multiple creative angles:
        
        Problem: {problem_description}
        Context: {json.dumps(context, indent=2)}
        
        Please provide a creative analysis including:
        1. Problem breakdown into components
        2. Root causes identification
        3. Constraints and limitations
        4. Hidden opportunities
        5. Creative insights
        6. Unconventional angles to approach the problem
        
        Respond in JSON format:
        {{
            "problem_breakdown": ["component1", "component2"],
            "root_causes": ["cause1", "cause2"],
            "constraints": ["constraint1", "constraint2"],
            "opportunities": ["opportunity1", "opportunity2"],
            "creative_insights": ["insight1", "insight2"],
            "unconventional_angles": ["angle1", "angle2"]
        }}
        """
        return prompt

    async def _generate_innovative_solutions(self, problem_description: str, creative_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate innovative solutions based on creative analysis."""
        try:
            innovative_solutions = []
            
            # Generate solutions based on creative insights
            insights = creative_analysis.get("creative_insights", [])
            opportunities = creative_analysis.get("opportunities", [])
            unconventional_angles = creative_analysis.get("unconventional_angles", [])
            
            # Create innovative solution for each insight
            for i, insight in enumerate(insights):
                solution = {
                    "id": f"innovative_{i}",
                    "type": "innovative",
                    "based_on": "creative_insight",
                    "insight": insight,
                    "solution": f"Innovative solution based on: {insight}",
                    "creativity_score": 0.7 + (i * 0.1),
                    "innovation_level": "high" if i < 2 else "moderate",
                    "feasibility": 0.6 + (i * 0.05),
                    "impact_potential": 0.8 - (i * 0.1)
                }
                innovative_solutions.append(solution)
            
            # Create solutions based on opportunities
            for i, opportunity in enumerate(opportunities):
                solution = {
                    "id": f"opportunity_{i}",
                    "type": "opportunity_based",
                    "based_on": "opportunity",
                    "opportunity": opportunity,
                    "solution": f"Solution leveraging: {opportunity}",
                    "creativity_score": 0.6 + (i * 0.1),
                    "innovation_level": "moderate",
                    "feasibility": 0.7 + (i * 0.05),
                    "impact_potential": 0.7 - (i * 0.1)
                }
                innovative_solutions.append(solution)
            
            # Create solutions based on unconventional angles
            for i, angle in enumerate(unconventional_angles):
                solution = {
                    "id": f"unconventional_{i}",
                    "type": "unconventional",
                    "based_on": "unconventional_angle",
                    "angle": angle,
                    "solution": f"Unconventional approach: {angle}",
                    "creativity_score": 0.9 - (i * 0.1),
                    "innovation_level": "very_high",
                    "feasibility": 0.4 + (i * 0.1),
                    "impact_potential": 0.9 - (i * 0.1)
                }
                innovative_solutions.append(solution)
            
            return innovative_solutions
            
        except Exception as e:
            logger.error(f"Error generating innovative solutions: {e}")
            return []

    async def _develop_adaptive_strategies(self, problem_description: str, innovative_solutions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Develop adaptive strategies that can evolve based on changing conditions."""
        try:
            adaptive_strategies = []
            
            for i, solution in enumerate(innovative_solutions):
                # Create adaptive strategy based on each innovative solution
                strategy = {
                    "id": f"adaptive_{i}",
                    "base_solution": solution,
                    "strategy_type": "adaptive",
                    "adaptation_mechanisms": [
                        "Dynamic parameter adjustment",
                        "Real-time feedback integration",
                        "Conditional branching",
                        "Performance-based evolution"
                    ],
                    "adaptation_triggers": [
                        "Performance degradation",
                        "Environmental changes",
                        "New constraints",
                        "Opportunity detection"
                    ],
                    "flexibility_score": 0.8 + (i * 0.05),
                    "robustness_score": 0.7 + (i * 0.05),
                    "evolution_capability": "high"
                }
                adaptive_strategies.append(strategy)
            
            # Add general adaptive strategies
            general_strategies = [
                {
                    "id": "adaptive_general_1",
                    "strategy_type": "multi_approach",
                    "description": "Maintain multiple solution approaches and switch based on conditions",
                    "adaptation_mechanisms": ["Solution switching", "Hybrid approaches", "Fallback mechanisms"],
                    "flexibility_score": 0.9,
                    "robustness_score": 0.8,
                    "evolution_capability": "very_high"
                },
                {
                    "id": "adaptive_general_2",
                    "strategy_type": "incremental_improvement",
                    "description": "Continuously improve solution based on feedback and results",
                    "adaptation_mechanisms": ["Feedback loops", "Performance monitoring", "Iterative refinement"],
                    "flexibility_score": 0.7,
                    "robustness_score": 0.9,
                    "evolution_capability": "high"
                }
            ]
            
            adaptive_strategies.extend(general_strategies)
            return adaptive_strategies
            
        except Exception as e:
            logger.error(f"Error developing adaptive strategies: {e}")
            return []

    async def _create_novel_approaches(self, problem_description: str, adaptive_strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create novel approaches that combine multiple strategies in unique ways."""
        try:
            novel_approaches = []
            
            # Create novel approaches by combining strategies
            for i, strategy in enumerate(adaptive_strategies):
                # Create novel approach based on each adaptive strategy
                approach = {
                    "id": f"novel_{i}",
                    "base_strategy": strategy,
                    "approach_type": "novel_combination",
                    "novel_elements": [
                        "Cross-domain knowledge integration",
                        "Emergent behavior utilization",
                        "Unconventional resource allocation",
                        "Creative constraint exploitation"
                    ],
                    "uniqueness_score": 0.8 + (i * 0.05),
                    "breakthrough_potential": 0.7 + (i * 0.05),
                    "risk_level": "moderate" if i < 3 else "high",
                    "description": f"Novel approach combining {strategy.get('strategy_type', 'adaptive')} with creative elements"
                }
                novel_approaches.append(approach)
            
            # Add completely novel approaches
            completely_novel = [
                {
                    "id": "novel_complete_1",
                    "approach_type": "paradigm_shift",
                    "description": "Completely new way of thinking about the problem",
                    "novel_elements": ["Paradigm shift", "Fundamental assumption challenge", "New problem framing"],
                    "uniqueness_score": 0.95,
                    "breakthrough_potential": 0.9,
                    "risk_level": "high",
                    "feasibility": 0.3
                },
                {
                    "id": "novel_complete_2",
                    "approach_type": "emergent_solution",
                    "description": "Let the solution emerge from system interactions",
                    "novel_elements": ["Emergent behavior", "Self-organizing systems", "Complexity utilization"],
                    "uniqueness_score": 0.9,
                    "breakthrough_potential": 0.8,
                    "risk_level": "high",
                    "feasibility": 0.4
                }
            ]
            
            novel_approaches.extend(completely_novel)
            return novel_approaches
            
        except Exception as e:
            logger.error(f"Error creating novel approaches: {e}")
            return []

    async def _select_best_creative_solution(self, innovative_solutions: List[Dict[str, Any]], 
                                           adaptive_strategies: List[Dict[str, Any]], 
                                           novel_approaches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best creative solution based on multiple criteria."""
        try:
            all_solutions = []
            
            # Combine all solution types
            for solution in innovative_solutions:
                solution["category"] = "innovative"
                all_solutions.append(solution)
            
            for strategy in adaptive_strategies:
                strategy["category"] = "adaptive"
                all_solutions.append(strategy)
            
            for approach in novel_approaches:
                approach["category"] = "novel"
                all_solutions.append(approach)
            
            if not all_solutions:
                return {"error": "No solutions available"}
            
            # Score each solution
            scored_solutions = []
            for solution in all_solutions:
                score = self._calculate_creative_solution_score(solution)
                solution["overall_score"] = score
                scored_solutions.append(solution)
            
            # Sort by score and select best
            scored_solutions.sort(key=lambda x: x["overall_score"], reverse=True)
            best_solution = scored_solutions[0]
            
            return best_solution
            
        except Exception as e:
            logger.error(f"Error selecting best creative solution: {e}")
            return {"error": str(e)}

    def _calculate_creative_solution_score(self, solution: Dict[str, Any]) -> float:
        """Calculate overall score for a creative solution."""
        try:
            # Base creativity score
            creativity_score = solution.get("creativity_score", 0.5)
            
            # Category-specific scoring
            category = solution.get("category", "unknown")
            
            if category == "innovative":
                feasibility = solution.get("feasibility", 0.5)
                impact_potential = solution.get("impact_potential", 0.5)
                score = (creativity_score * 0.4 + feasibility * 0.3 + impact_potential * 0.3)
            
            elif category == "adaptive":
                flexibility = solution.get("flexibility_score", 0.5)
                robustness = solution.get("robustness_score", 0.5)
                score = (creativity_score * 0.3 + flexibility * 0.35 + robustness * 0.35)
            
            elif category == "novel":
                uniqueness = solution.get("uniqueness_score", 0.5)
                breakthrough_potential = solution.get("breakthrough_potential", 0.5)
                feasibility = solution.get("feasibility", 0.5)
                score = (creativity_score * 0.3 + uniqueness * 0.3 + breakthrough_potential * 0.25 + feasibility * 0.15)
            
            else:
                score = creativity_score
            
            return min(1.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating creative solution score: {e}")
            return 0.5

    async def _learn_from_creative_solution(self, creative_solution: Dict[str, Any]) -> None:
        """Learn from creative solutions to improve future creative problem solving."""
        try:
            solution_id = creative_solution["id"]
            
            # Extract learning insights
            learning_insights = {
                "solution_id": solution_id,
                "creativity_score": creative_solution.get("creativity_score", 0.0),
                "innovation_level": creative_solution.get("innovation_level", "moderate"),
                "problem_type": self._categorize_problem_type(creative_solution["problem_description"]),
                "solution_category": creative_solution["selected_solution"].get("category", "unknown"),
                "timestamp": datetime.now()
            }
            
            # Store learning data
            self.creative_learning[solution_id] = learning_insights
            
            # Update creative learning patterns
            await self._update_creative_learning_patterns(learning_insights)
            
            logger.debug(f"Creative learning data stored for solution {solution_id}")
            
        except Exception as e:
            logger.error(f"Error learning from creative solution: {e}")

    def _categorize_problem_type(self, problem_description: str) -> str:
        """Categorize the type of problem for learning purposes."""
        problem_lower = problem_description.lower()
        
        if any(word in problem_lower for word in ["optimization", "efficiency", "performance"]):
            return "optimization"
        elif any(word in problem_lower for word in ["error", "failure", "bug", "issue"]):
            return "troubleshooting"
        elif any(word in problem_lower for word in ["design", "architecture", "structure"]):
            return "design"
        elif any(word in problem_lower for word in ["integration", "compatibility", "interface"]):
            return "integration"
        else:
            return "general"

    async def _update_creative_learning_patterns(self, learning_insights: Dict[str, Any]) -> None:
        """Update creative learning patterns based on solution outcomes."""
        try:
            problem_type = learning_insights.get("problem_type", "general")
            solution_category = learning_insights.get("solution_category", "unknown")
            creativity_score = learning_insights.get("creativity_score", 0.0)
            
            # Create pattern key
            pattern_key = f"{problem_type}_{solution_category}"
            
            if pattern_key not in self.creative_learning:
                self.creative_learning[pattern_key] = {
                    "count": 0,
                    "total_creativity_score": 0,
                    "success_rate": 0,
                    "best_approaches": []
                }
            
            pattern = self.creative_learning[pattern_key]
            pattern["count"] += 1
            pattern["total_creativity_score"] += creativity_score
            
            # Update success rate (assuming high creativity score indicates success)
            if creativity_score >= 0.7:
                pattern["success_rate"] = (pattern["success_rate"] * (pattern["count"] - 1) + 1) / pattern["count"]
            else:
                pattern["success_rate"] = (pattern["success_rate"] * (pattern["count"] - 1)) / pattern["count"]
            
            logger.debug(f"Updated creative learning pattern: {pattern_key}")
            
        except Exception as e:
            logger.error(f"Error updating creative learning patterns: {e}")

    async def get_creative_problem_solving_report(self) -> Dict[str, Any]:
        """Get a comprehensive report on creative problem solving capabilities."""
        try:
            total_solutions = len(self.creative_solutions)
            total_innovations = len(self.innovation_history)
            
            # Calculate average creativity scores
            creativity_scores = [sol.get("creativity_score", 0.0) for sol in self.creative_solutions.values()]
            avg_creativity = sum(creativity_scores) / len(creativity_scores) if creativity_scores else 0.0
            
            # Analyze innovation levels
            innovation_levels = {}
            for solution in self.creative_solutions.values():
                level = solution.get("innovation_level", "unknown")
                innovation_levels[level] = innovation_levels.get(level, 0) + 1
            
            # Get recent creative solutions
            recent_solutions = list(self.creative_solutions.values())[-5:]
            
            report = {
                "total_creative_solutions": total_solutions,
                "total_innovations": total_innovations,
                "average_creativity_score": avg_creativity,
                "innovation_level_distribution": innovation_levels,
                "recent_solutions": [
                    {
                        "id": sol["id"],
                        "problem": sol["problem_description"][:100] + "...",
                        "creativity_score": sol.get("creativity_score", 0.0),
                        "innovation_level": sol.get("innovation_level", "unknown"),
                        "timestamp": sol["timestamp"].isoformat()
                    }
                    for sol in recent_solutions
                ],
                "learning_patterns": len(self.creative_learning),
                "timestamp": datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating creative problem solving report: {e}")
            return {"error": str(e)} 

    # ============================================================================
    # PHASE 6.1: ADVANCED AUTOMATION
    # ============================================================================

    async def create_system_automation(self, automation_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create system-wide automation with intelligent orchestration."""
        try:
            automation_id = str(uuid.uuid4())
            
            # Create automation workflow
            automation = {
                "id": automation_id,
                "type": automation_type,
                "config": config,
                "status": "active",
                "created_at": datetime.now(),
                "last_executed": None,
                "execution_count": 0,
                "success_rate": 0.0,
                "performance_metrics": {},
                "orchestration_rules": config.get("orchestration_rules", []),
                "resource_requirements": config.get("resource_requirements", {}),
                "scheduling_config": config.get("scheduling", {})
            }
            
            # Initialize automation components
            await self._initialize_automation_components(automation)
            
            # Store automation
            self.automation_workflows[automation_id] = automation
            
            # Add to automation history
            self.automation_history.append({
                "action": "created",
                "automation_id": automation_id,
                "type": automation_type,
                "timestamp": datetime.now()
            })
            
            logger.info(f"System automation created: {automation_type} (ID: {automation_id})")
            return {"automation_id": automation_id, "status": "created"}
            
        except Exception as e:
            logger.error(f"Error creating system automation: {e}")
            return {"error": str(e)}

    async def _initialize_automation_components(self, automation: Dict[str, Any]) -> None:
        """Initialize automation components including orchestration and scheduling."""
        try:
            automation_id = automation["id"]
            automation_type = automation["type"]
            
            # Initialize task scheduler
            self.task_scheduler[automation_id] = {
                "automation_id": automation_id,
                "scheduled_tasks": [],
                "execution_queue": [],
                "priority_queue": [],
                "resource_allocation": {},
                "performance_tracking": {}
            }
            
            # Initialize resource optimizer
            self.resource_optimizer[automation_id] = {
                "automation_id": automation_id,
                "resource_usage": {},
                "optimization_rules": [],
                "efficiency_metrics": {},
                "optimization_history": []
            }
            
            # Initialize system orchestrator
            self.system_orchestrator[automation_id] = {
                "automation_id": automation_id,
                "orchestration_rules": automation.get("orchestration_rules", []),
                "agent_coordination": {},
                "workflow_management": {},
                "coordination_history": []
            }
            
            logger.debug(f"Automation components initialized for {automation_id}")
            
        except Exception as e:
            logger.error(f"Error initializing automation components: {e}")

    async def execute_intelligent_orchestration(self, automation_id: str) -> Dict[str, Any]:
        """Execute intelligent orchestration for system-wide automation."""
        try:
            if automation_id not in self.automation_workflows:
                return {"error": "Automation not found"}
            
            automation = self.automation_workflows[automation_id]
            orchestrator = self.system_orchestrator.get(automation_id, {})
            
            # Perform intelligent orchestration
            orchestration_result = await self._perform_intelligent_orchestration(automation, orchestrator)
            
            # Update automation status
            automation["last_executed"] = datetime.now()
            automation["execution_count"] += 1
            
            # Update success rate
            if orchestration_result.get("success", False):
                current_success_rate = automation["success_rate"]
                execution_count = automation["execution_count"]
                automation["success_rate"] = (current_success_rate * (execution_count - 1) + 1) / execution_count
            else:
                current_success_rate = automation["success_rate"]
                execution_count = automation["execution_count"]
                automation["success_rate"] = (current_success_rate * (execution_count - 1)) / execution_count
            
            # Store orchestration result
            orchestrator["coordination_history"].append({
                "timestamp": datetime.now(),
                "result": orchestration_result,
                "performance_metrics": orchestration_result.get("performance_metrics", {})
            })
            
            logger.info(f"Intelligent orchestration executed for {automation_id}")
            return orchestration_result
            
        except Exception as e:
            logger.error(f"Error executing intelligent orchestration: {e}")
            return {"error": str(e)}

    async def _perform_intelligent_orchestration(self, automation: Dict[str, Any], orchestrator: Dict[str, Any]) -> Dict[str, Any]:
        """Perform intelligent orchestration based on automation type and rules."""
        try:
            automation_type = automation["type"]
            orchestration_rules = orchestrator.get("orchestration_rules", [])
            
            # Get current system state
            system_state = await self._get_system_state()
            
            # Apply orchestration rules
            orchestration_actions = []
            for rule in orchestration_rules:
                action = await self._apply_orchestration_rule(rule, system_state, automation)
                if action:
                    orchestration_actions.append(action)
            
            # Execute orchestration actions
            execution_results = []
            for action in orchestration_actions:
                result = await self._execute_orchestration_action(action)
                execution_results.append(result)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_orchestration_performance(execution_results)
            
            orchestration_result = {
                "automation_id": automation["id"],
                "automation_type": automation_type,
                "actions_executed": len(orchestration_actions),
                "execution_results": execution_results,
                "performance_metrics": performance_metrics,
                "success": all(r.get("success", False) for r in execution_results),
                "timestamp": datetime.now().isoformat()
            }
            
            return orchestration_result
            
        except Exception as e:
            logger.error(f"Error performing intelligent orchestration: {e}")
            return {"error": str(e), "success": False}

    async def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state for orchestration decisions."""
        try:
            # Get agent statuses
            agent_statuses = {}
            for agent_name in ["research", "signal", "strategy", "risk", "execution", "compliance", "monitor", "optimize"]:
                try:
                    status = await self.get_agent_intelligence_report(agent_name)
                    agent_statuses[agent_name] = status
                except Exception:
                    agent_statuses[agent_name] = {"status": "unknown"}
            
            # Get resource usage
            resource_usage = await self._get_resource_usage()
            
            # Get current tasks
            current_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.IN_PROGRESS]
            
            system_state = {
                "agent_statuses": agent_statuses,
                "resource_usage": resource_usage,
                "current_tasks": len(current_tasks),
                "system_load": len(current_tasks) / 10.0,  # Normalized load
                "timestamp": datetime.now()
            }
            
            return system_state
            
        except Exception as e:
            logger.error(f"Error getting system state: {e}")
            return {"error": str(e)}

    async def _apply_orchestration_rule(self, rule: Dict[str, Any], system_state: Dict[str, Any], automation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply an orchestration rule to determine actions."""
        try:
            rule_type = rule.get("type", "default")
            conditions = rule.get("conditions", {})
            
            # Check if conditions are met
            if not self._check_orchestration_conditions(conditions, system_state):
                return None
            
            # Generate action based on rule type
            if rule_type == "resource_optimization":
                return await self._generate_resource_optimization_action(rule, system_state)
            elif rule_type == "task_scheduling":
                return await self._generate_task_scheduling_action(rule, system_state)
            elif rule_type == "agent_coordination":
                return await self._generate_agent_coordination_action(rule, system_state)
            elif rule_type == "workflow_management":
                return await self._generate_workflow_management_action(rule, system_state)
            else:
                return await self._generate_default_orchestration_action(rule, system_state)
                
        except Exception as e:
            logger.error(f"Error applying orchestration rule: {e}")
            return None

    def _check_orchestration_conditions(self, conditions: Dict[str, Any], system_state: Dict[str, Any]) -> bool:
        """Check if orchestration conditions are met."""
        try:
            for condition_key, condition_value in conditions.items():
                if condition_key == "system_load_threshold":
                    if system_state.get("system_load", 0) < condition_value:
                        return False
                elif condition_key == "agent_availability":
                    required_agents = condition_value
                    agent_statuses = system_state.get("agent_statuses", {})
                    for agent in required_agents:
                        if agent not in agent_statuses or agent_statuses[agent].get("status") != "healthy":
                            return False
                elif condition_key == "resource_available":
                    required_resources = condition_value
                    resource_usage = system_state.get("resource_usage", {})
                    for resource, threshold in required_resources.items():
                        if resource_usage.get(resource, 0) > threshold:
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking orchestration conditions: {e}")
            return False

    async def _generate_resource_optimization_action(self, rule: Dict[str, Any], system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate resource optimization action."""
        return {
            "type": "resource_optimization",
            "action": "optimize_resource_allocation",
            "target_resources": rule.get("target_resources", []),
            "optimization_strategy": rule.get("strategy", "efficient"),
            "priority": rule.get("priority", "medium")
        }

    async def _generate_task_scheduling_action(self, rule: Dict[str, Any], system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate task scheduling action."""
        return {
            "type": "task_scheduling",
            "action": "schedule_tasks",
            "task_types": rule.get("task_types", []),
            "scheduling_strategy": rule.get("strategy", "priority_based"),
            "priority": rule.get("priority", "medium")
        }

    async def _generate_agent_coordination_action(self, rule: Dict[str, Any], system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate agent coordination action."""
        return {
            "type": "agent_coordination",
            "action": "coordinate_agents",
            "target_agents": rule.get("target_agents", []),
            "coordination_type": rule.get("coordination_type", "collaborative"),
            "priority": rule.get("priority", "medium")
        }

    async def _generate_workflow_management_action(self, rule: Dict[str, Any], system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate workflow management action."""
        return {
            "type": "workflow_management",
            "action": "manage_workflow",
            "workflow_type": rule.get("workflow_type", "default"),
            "management_strategy": rule.get("strategy", "adaptive"),
            "priority": rule.get("priority", "medium")
        }

    async def _generate_default_orchestration_action(self, rule: Dict[str, Any], system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default orchestration action."""
        return {
            "type": "default",
            "action": "system_maintenance",
            "maintenance_type": rule.get("maintenance_type", "general"),
            "priority": rule.get("priority", "low")
        }

    async def _execute_orchestration_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an orchestration action."""
        try:
            action_type = action.get("type", "default")
            
            if action_type == "resource_optimization":
                return await self._execute_resource_optimization(action)
            elif action_type == "task_scheduling":
                return await self._execute_task_scheduling(action)
            elif action_type == "agent_coordination":
                return await self._execute_agent_coordination(action)
            elif action_type == "workflow_management":
                return await self._execute_workflow_management(action)
            else:
                return await self._execute_default_action(action)
                
        except Exception as e:
            logger.error(f"Error executing orchestration action: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_resource_optimization(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute resource optimization action."""
        try:
            target_resources = action.get("target_resources", [])
            strategy = action.get("optimization_strategy", "efficient")
            
            # Simulate resource optimization
            optimization_results = {}
            for resource in target_resources:
                optimization_results[resource] = {
                    "before": 0.7,  # Simulated current usage
                    "after": 0.5,   # Simulated optimized usage
                    "improvement": 0.2
                }
            
            return {
                "success": True,
                "action_type": "resource_optimization",
                "results": optimization_results,
                "strategy_used": strategy,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_task_scheduling(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task scheduling action."""
        try:
            task_types = action.get("task_types", [])
            strategy = action.get("scheduling_strategy", "priority_based")
            
            # Simulate task scheduling
            scheduled_tasks = []
            for task_type in task_types:
                scheduled_tasks.append({
                    "task_type": task_type,
                    "priority": "medium",
                    "estimated_duration": "5 minutes",
                    "assigned_agents": ["research", "signal"]
                })
            
            return {
                "success": True,
                "action_type": "task_scheduling",
                "scheduled_tasks": scheduled_tasks,
                "strategy_used": strategy,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_agent_coordination(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent coordination action."""
        try:
            target_agents = action.get("target_agents", [])
            coordination_type = action.get("coordination_type", "collaborative")
            
            # Simulate agent coordination
            coordination_results = {}
            for agent in target_agents:
                coordination_results[agent] = {
                    "status": "coordinated",
                    "coordination_type": coordination_type,
                    "performance_impact": "positive"
                }
            
            return {
                "success": True,
                "action_type": "agent_coordination",
                "coordinated_agents": coordination_results,
                "coordination_type": coordination_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_workflow_management(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow management action."""
        try:
            workflow_type = action.get("workflow_type", "default")
            strategy = action.get("management_strategy", "adaptive")
            
            # Simulate workflow management
            workflow_status = {
                "workflow_type": workflow_type,
                "status": "managed",
                "strategy_used": strategy,
                "efficiency_improvement": 0.15
            }
            
            return {
                "success": True,
                "action_type": "workflow_management",
                "workflow_status": workflow_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_default_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute default orchestration action."""
        try:
            maintenance_type = action.get("maintenance_type", "general")
            
            # Simulate system maintenance
            maintenance_result = {
                "maintenance_type": maintenance_type,
                "status": "completed",
                "impact": "minimal"
            }
            
            return {
                "success": True,
                "action_type": "system_maintenance",
                "maintenance_result": maintenance_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_orchestration_performance(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate orchestration performance metrics."""
        try:
            total_actions = len(execution_results)
            successful_actions = sum(1 for r in execution_results if r.get("success", False))
            success_rate = successful_actions / total_actions if total_actions > 0 else 0
            
            # Calculate average execution time (simulated)
            avg_execution_time = 0.5  # Simulated average time in seconds
            
            performance_metrics = {
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time,
                "efficiency_score": success_rate * (1.0 - avg_execution_time / 10.0)  # Normalized efficiency
            }
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Error calculating orchestration performance: {e}")
            return {"error": str(e)}

    async def _get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage across the system."""
        try:
            # Simulate resource usage monitoring
            resource_usage = {
                "cpu_usage": 0.65,
                "memory_usage": 0.72,
                "network_usage": 0.45,
                "disk_usage": 0.38,
                "agent_load": 0.58
            }
            
            return resource_usage
            
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {"error": str(e)}

    async def schedule_automated_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule automated tasks with intelligent resource allocation."""
        try:
            task_id = str(uuid.uuid4())
            
            # Create scheduled task
            scheduled_task = {
                "id": task_id,
                "name": task_config.get("name", "automated_task"),
                "type": task_config.get("type", "general"),
                "schedule": task_config.get("schedule", "immediate"),
                "priority": task_config.get("priority", "medium"),
                "resource_requirements": task_config.get("resource_requirements", {}),
                "dependencies": task_config.get("dependencies", []),
                "status": "scheduled",
                "created_at": datetime.now(),
                "next_execution": datetime.now(),
                "execution_history": []
            }
            
            # Add to task scheduler
            if task_id not in self.task_scheduler:
                self.task_scheduler[task_id] = {
                    "automation_id": "system_scheduler",
                    "scheduled_tasks": [],
                    "execution_queue": [],
                    "priority_queue": [],
                    "resource_allocation": {},
                    "performance_tracking": {}
                }
            
            self.task_scheduler[task_id]["scheduled_tasks"].append(scheduled_task)
            
            # Optimize resource allocation
            await self._optimize_resource_allocation(task_id, scheduled_task)
            
            logger.info(f"Automated task scheduled: {scheduled_task['name']} (ID: {task_id})")
            return {"task_id": task_id, "status": "scheduled"}
            
        except Exception as e:
            logger.error(f"Error scheduling automated task: {e}")
            return {"error": str(e)}

    async def _optimize_resource_allocation(self, task_id: str, task: Dict[str, Any]) -> None:
        """Optimize resource allocation for scheduled tasks."""
        try:
            resource_requirements = task.get("resource_requirements", {})
            
            # Calculate optimal resource allocation
            optimal_allocation = {}
            for resource, requirement in resource_requirements.items():
                # Simple optimization logic - could be enhanced with ML
                if resource == "cpu":
                    optimal_allocation[resource] = min(requirement, 0.8)  # Cap at 80%
                elif resource == "memory":
                    optimal_allocation[resource] = min(requirement, 0.75)  # Cap at 75%
                elif resource == "network":
                    optimal_allocation[resource] = min(requirement, 0.6)   # Cap at 60%
                else:
                    optimal_allocation[resource] = requirement
            
            # Store optimal allocation
            if task_id in self.task_scheduler:
                self.task_scheduler[task_id]["resource_allocation"] = optimal_allocation
            
            logger.debug(f"Resource allocation optimized for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {e}")

    async def get_automation_report(self) -> Dict[str, Any]:
        """Get comprehensive automation report."""
        try:
            total_automations = len(self.automation_workflows)
            active_automations = sum(1 for a in self.automation_workflows.values() if a.get("status") == "active")
            
            # Calculate average success rate
            success_rates = [a.get("success_rate", 0.0) for a in self.automation_workflows.values()]
            avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
            
            # Get recent automation activities
            recent_activities = self.automation_history[-10:] if self.automation_history else []
            
            automation_report = {
                "total_automations": total_automations,
                "active_automations": active_automations,
                "average_success_rate": avg_success_rate,
                "automation_types": list(set(a.get("type") for a in self.automation_workflows.values())),
                "recent_activities": recent_activities,
                "resource_optimization_count": len(self.resource_optimizer),
                "task_scheduling_count": len(self.task_scheduler),
                "orchestration_count": len(self.system_orchestrator),
                "timestamp": datetime.now().isoformat()
            }
            
            return automation_report
            
        except Exception as e:
            logger.error(f"Error generating automation report: {e}")
            return {"error": str(e)}

    # ============================================================================
    # PHASE 6.2: INTELLIGENT WORKFLOWS
    # ============================================================================

    async def create_intelligent_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent workflow with dynamic adaptation and learning capabilities."""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Create intelligent workflow
            workflow = {
                "id": workflow_id,
                "name": workflow_config.get("name", "intelligent_workflow"),
                "type": workflow_config.get("type", "general"),
                "description": workflow_config.get("description", ""),
                "steps": workflow_config.get("steps", []),
                "conditions": workflow_config.get("conditions", {}),
                "adaptation_rules": workflow_config.get("adaptation_rules", []),
                "optimization_strategy": workflow_config.get("optimization_strategy", "adaptive"),
                "learning_enabled": workflow_config.get("learning_enabled", True),
                "status": "active",
                "created_at": datetime.now(),
                "last_executed": None,
                "execution_count": 0,
                "success_rate": 0.0,
                "performance_metrics": {},
                "adaptation_history": [],
                "learning_insights": []
            }
            
            # Initialize workflow components
            await self._initialize_workflow_components(workflow)
            
            # Store workflow
            self.intelligent_workflows[workflow_id] = workflow
            
            # Add to workflow history
            self.workflow_history.append({
                "action": "created",
                "workflow_id": workflow_id,
                "type": workflow["type"],
                "timestamp": datetime.now()
            })
            
            logger.info(f"Intelligent workflow created: {workflow['name']} (ID: {workflow_id})")
            return {"workflow_id": workflow_id, "status": "created"}
            
        except Exception as e:
            logger.error(f"Error creating intelligent workflow: {e}")
            return {"error": str(e)}

    async def _initialize_workflow_components(self, workflow: Dict[str, Any]) -> None:
        """Initialize workflow components including optimizer, monitor, and learning."""
        try:
            workflow_id = workflow["id"]
            
            # Initialize workflow optimizer
            self.workflow_optimizer[workflow_id] = {
                "workflow_id": workflow_id,
                "optimization_rules": workflow.get("adaptation_rules", []),
                "performance_targets": {},
                "optimization_history": [],
                "efficiency_metrics": {}
            }
            
            # Initialize workflow monitor
            self.workflow_monitor[workflow_id] = {
                "workflow_id": workflow_id,
                "monitoring_rules": [],
                "performance_metrics": {},
                "alert_thresholds": {},
                "monitoring_history": []
            }
            
            # Initialize workflow learning
            self.workflow_learning[workflow_id] = {
                "workflow_id": workflow_id,
                "learning_patterns": {},
                "improvement_suggestions": [],
                "learning_history": [],
                "adaptation_insights": []
            }
            
            logger.debug(f"Workflow components initialized for {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error initializing workflow components: {e}")

    async def execute_intelligent_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute intelligent workflow with dynamic adaptation and optimization."""
        try:
            if workflow_id not in self.intelligent_workflows:
                return {"error": "Workflow not found"}
            
            workflow = self.intelligent_workflows[workflow_id]
            optimizer = self.workflow_optimizer.get(workflow_id, {})
            monitor = self.workflow_monitor.get(workflow_id, {})
            
            # Execute workflow with intelligent adaptation
            execution_result = await self._execute_workflow_with_adaptation(workflow, optimizer, context)
            
            # Monitor workflow performance
            monitoring_result = await self._monitor_workflow_performance(workflow, monitor, execution_result)
            
            # Optimize workflow based on results
            optimization_result = await self._optimize_workflow(workflow, optimizer, execution_result, monitoring_result)
            
            # Learn from workflow execution
            learning_result = await self._learn_from_workflow_execution(workflow, execution_result, optimization_result)
            
            # Update workflow status
            workflow["last_executed"] = datetime.now()
            workflow["execution_count"] += 1
            
            # Update success rate
            if execution_result.get("success", False):
                current_success_rate = workflow["success_rate"]
                execution_count = workflow["execution_count"]
                workflow["success_rate"] = (current_success_rate * (execution_count - 1) + 1) / execution_count
            else:
                current_success_rate = workflow["success_rate"]
                execution_count = workflow["execution_count"]
                workflow["success_rate"] = (current_success_rate * (execution_count - 1)) / execution_count
            
            # Store execution results
            workflow["adaptation_history"].append({
                "timestamp": datetime.now(),
                "execution_result": execution_result,
                "monitoring_result": monitoring_result,
                "optimization_result": optimization_result,
                "learning_result": learning_result
            })
            
            logger.info(f"Intelligent workflow executed: {workflow['name']} (ID: {workflow_id})")
            return {
                "workflow_id": workflow_id,
                "execution_result": execution_result,
                "monitoring_result": monitoring_result,
                "optimization_result": optimization_result,
                "learning_result": learning_result,
                "success": execution_result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"Error executing intelligent workflow: {e}")
            return {"error": str(e)}

    async def _execute_workflow_with_adaptation(self, workflow: Dict[str, Any], optimizer: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute workflow with dynamic adaptation based on conditions and optimization rules."""
        try:
            steps = workflow.get("steps", [])
            conditions = workflow.get("conditions", {})
            adaptation_rules = optimizer.get("optimization_rules", [])
            
            # Check workflow conditions
            if not self._check_workflow_conditions(conditions, context):
                return {"success": False, "error": "Workflow conditions not met"}
            
            # Execute workflow steps with adaptation
            execution_results = []
            adapted_steps = self._adapt_workflow_steps(steps, adaptation_rules, context)
            
            for step in adapted_steps:
                step_result = await self._execute_workflow_step(step, context)
                execution_results.append(step_result)
                
                # Check if step failed and apply adaptation
                if not step_result.get("success", False):
                    adaptation_result = await self._apply_workflow_adaptation(workflow, step, step_result, adaptation_rules)
                    if adaptation_result.get("success", False):
                        # Retry step with adaptation
                        step_result = await self._execute_workflow_step(adaptation_result["adapted_step"], context)
                        execution_results[-1] = step_result
            
            # Calculate overall execution metrics
            execution_metrics = self._calculate_workflow_execution_metrics(execution_results)
            
            execution_result = {
                "workflow_id": workflow["id"],
                "steps_executed": len(execution_results),
                "successful_steps": sum(1 for r in execution_results if r.get("success", False)),
                "execution_results": execution_results,
                "execution_metrics": execution_metrics,
                "adaptations_applied": len([r for r in execution_results if r.get("adaptation_applied", False)]),
                "success": all(r.get("success", False) for r in execution_results),
                "timestamp": datetime.now().isoformat()
            }
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error executing workflow with adaptation: {e}")
            return {"success": False, "error": str(e)}

    def _check_workflow_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any] = None) -> bool:
        """Check if workflow conditions are met."""
        try:
            if not conditions:
                return True
            
            context = context or {}
            
            for condition_key, condition_value in conditions.items():
                if condition_key == "system_load":
                    if context.get("system_load", 0) > condition_value:
                        return False
                elif condition_key == "agent_availability":
                    required_agents = condition_value
                    available_agents = context.get("available_agents", [])
                    for agent in required_agents:
                        if agent not in available_agents:
                            return False
                elif condition_key == "resource_available":
                    required_resources = condition_value
                    available_resources = context.get("available_resources", {})
                    for resource, threshold in required_resources.items():
                        if available_resources.get(resource, 0) < threshold:
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking workflow conditions: {e}")
            return False

    def _adapt_workflow_steps(self, steps: List[Dict[str, Any]], adaptation_rules: List[Dict[str, Any]], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Adapt workflow steps based on rules and context."""
        try:
            adapted_steps = steps.copy()
            context = context or {}
            
            for rule in adaptation_rules:
                rule_type = rule.get("type", "default")
                
                if rule_type == "step_optimization":
                    adapted_steps = self._optimize_workflow_steps(adapted_steps, rule, context)
                elif rule_type == "step_reordering":
                    adapted_steps = self._reorder_workflow_steps(adapted_steps, rule, context)
                elif rule_type == "step_skipping":
                    adapted_steps = self._skip_workflow_steps(adapted_steps, rule, context)
                elif rule_type == "step_addition":
                    adapted_steps = self._add_workflow_steps(adapted_steps, rule, context)
            
            return adapted_steps
            
        except Exception as e:
            logger.error(f"Error adapting workflow steps: {e}")
            return steps

    def _optimize_workflow_steps(self, steps: List[Dict[str, Any]], rule: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize workflow steps based on rule."""
        try:
            optimization_type = rule.get("optimization_type", "efficiency")
            
            if optimization_type == "efficiency":
                # Optimize for efficiency
                for step in steps:
                    if "timeout" in step:
                        step["timeout"] = min(step["timeout"], 30)  # Cap timeout at 30 seconds
                    if "retries" in step:
                        step["retries"] = min(step["retries"], 3)   # Cap retries at 3
            
            elif optimization_type == "reliability":
                # Optimize for reliability
                for step in steps:
                    if "retries" not in step:
                        step["retries"] = 3
                    if "timeout" not in step:
                        step["timeout"] = 60
            
            return steps
            
        except Exception as e:
            logger.error(f"Error optimizing workflow steps: {e}")
            return steps

    def _reorder_workflow_steps(self, steps: List[Dict[str, Any]], rule: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Reorder workflow steps based on rule."""
        try:
            reorder_strategy = rule.get("strategy", "priority")
            
            if reorder_strategy == "priority":
                # Sort by priority (higher priority first)
                steps.sort(key=lambda x: x.get("priority", 0), reverse=True)
            elif reorder_strategy == "dependency":
                # Sort by dependencies
                steps.sort(key=lambda x: len(x.get("dependencies", [])))
            
            return steps
            
        except Exception as e:
            logger.error(f"Error reordering workflow steps: {e}")
            return steps

    def _skip_workflow_steps(self, steps: List[Dict[str, Any]], rule: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Skip workflow steps based on rule."""
        try:
            skip_conditions = rule.get("skip_conditions", {})
            
            filtered_steps = []
            for step in steps:
                should_skip = False
                
                for condition_key, condition_value in skip_conditions.items():
                    if condition_key == "step_type" and step.get("type") == condition_value:
                        should_skip = True
                    elif condition_key == "step_priority" and step.get("priority", 0) < condition_value:
                        should_skip = True
                
                if not should_skip:
                    filtered_steps.append(step)
            
            return filtered_steps
            
        except Exception as e:
            logger.error(f"Error skipping workflow steps: {e}")
            return steps

    def _add_workflow_steps(self, steps: List[Dict[str, Any]], rule: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add workflow steps based on rule."""
        try:
            additional_steps = rule.get("additional_steps", [])
            
            # Add steps at specified positions
            for additional_step in additional_steps:
                position = additional_step.get("position", "end")
                
                if position == "end":
                    steps.append(additional_step["step"])
                elif position == "beginning":
                    steps.insert(0, additional_step["step"])
                elif isinstance(position, int) and 0 <= position < len(steps):
                    steps.insert(position, additional_step["step"])
            
            return steps
            
        except Exception as e:
            logger.error(f"Error adding workflow steps: {e}")
            return steps

    async def _execute_workflow_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            step_type = step.get("type", "default")
            step_name = step.get("name", "unknown_step")
            
            # Simulate step execution
            execution_time = 0.5  # Simulated execution time
            success = True  # Simulated success
            
            # Simulate occasional failures
            if step.get("failure_rate", 0) > 0:
                import random
                if random.random() < step["failure_rate"]:
                    success = False
            
            step_result = {
                "step_name": step_name,
                "step_type": step_type,
                "success": success,
                "execution_time": execution_time,
                "adaptation_applied": False,
                "timestamp": datetime.now().isoformat()
            }
            
            if not success:
                step_result["error"] = f"Step {step_name} failed"
            
            return step_result
            
        except Exception as e:
            return {
                "step_name": step.get("name", "unknown"),
                "step_type": step.get("type", "default"),
                "success": False,
                "error": str(e),
                "adaptation_applied": False,
                "timestamp": datetime.now().isoformat()
            }

    async def _apply_workflow_adaptation(self, workflow: Dict[str, Any], step: Dict[str, Any], step_result: Dict[str, Any], adaptation_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply workflow adaptation when a step fails."""
        try:
            # Find applicable adaptation rules
            applicable_rules = []
            for rule in adaptation_rules:
                if rule.get("trigger") == "step_failure" and step.get("type") in rule.get("step_types", []):
                    applicable_rules.append(rule)
            
            if not applicable_rules:
                return {"success": False, "error": "No applicable adaptation rules"}
            
            # Apply first applicable rule
            rule = applicable_rules[0]
            adaptation_type = rule.get("adaptation_type", "retry")
            
            if adaptation_type == "retry":
                adapted_step = step.copy()
                adapted_step["retries"] = adapted_step.get("retries", 0) + 1
                adapted_step["timeout"] = adapted_step.get("timeout", 30) * 1.5  # Increase timeout
                
                return {
                    "success": True,
                    "adaptation_type": "retry",
                    "adapted_step": adapted_step,
                    "rule_applied": rule
                }
            
            elif adaptation_type == "skip":
                return {
                    "success": True,
                    "adaptation_type": "skip",
                    "adapted_step": None,
                    "rule_applied": rule
                }
            
            elif adaptation_type == "replace":
                replacement_step = rule.get("replacement_step", {})
                return {
                    "success": True,
                    "adaptation_type": "replace",
                    "adapted_step": replacement_step,
                    "rule_applied": rule
                }
            
            return {"success": False, "error": "Unknown adaptation type"}
            
        except Exception as e:
            logger.error(f"Error applying workflow adaptation: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_workflow_execution_metrics(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate workflow execution metrics."""
        try:
            total_steps = len(execution_results)
            successful_steps = sum(1 for r in execution_results if r.get("success", False))
            total_execution_time = sum(r.get("execution_time", 0) for r in execution_results)
            adaptations_applied = sum(1 for r in execution_results if r.get("adaptation_applied", False))
            
            metrics = {
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "success_rate": successful_steps / total_steps if total_steps > 0 else 0,
                "total_execution_time": total_execution_time,
                "average_step_time": total_execution_time / total_steps if total_steps > 0 else 0,
                "adaptations_applied": adaptations_applied,
                "adaptation_rate": adaptations_applied / total_steps if total_steps > 0 else 0
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating workflow execution metrics: {e}")
            return {"error": str(e)}

    async def _monitor_workflow_performance(self, workflow: Dict[str, Any], monitor: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor workflow performance and generate alerts."""
        try:
            execution_metrics = execution_result.get("execution_metrics", {})
            
            # Check performance thresholds
            alerts = []
            performance_score = 0.0
            
            # Check success rate
            success_rate = execution_metrics.get("success_rate", 0.0)
            if success_rate < 0.8:
                alerts.append({
                    "type": "low_success_rate",
                    "severity": "warning",
                    "message": f"Workflow success rate is {success_rate:.2%}, below threshold of 80%"
                })
            
            # Check execution time
            avg_step_time = execution_metrics.get("average_step_time", 0.0)
            if avg_step_time > 5.0:  # More than 5 seconds per step
                alerts.append({
                    "type": "high_execution_time",
                    "severity": "warning",
                    "message": f"Average step execution time is {avg_step_time:.2f}s, above threshold"
                })
            
            # Check adaptation rate
            adaptation_rate = execution_metrics.get("adaptation_rate", 0.0)
            if adaptation_rate > 0.3:  # More than 30% adaptations
                alerts.append({
                    "type": "high_adaptation_rate",
                    "severity": "info",
                    "message": f"High adaptation rate: {adaptation_rate:.2%}"
                })
            
            # Calculate performance score
            performance_score = (
                success_rate * 0.5 +
                (1.0 - min(avg_step_time / 10.0, 1.0)) * 0.3 +
                (1.0 - adaptation_rate) * 0.2
            )
            
            monitoring_result = {
                "workflow_id": workflow["id"],
                "performance_score": performance_score,
                "alerts": alerts,
                "metrics": execution_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store monitoring data
            monitor["monitoring_history"].append(monitoring_result)
            
            return monitoring_result
            
        except Exception as e:
            logger.error(f"Error monitoring workflow performance: {e}")
            return {"error": str(e)}

    async def _optimize_workflow(self, workflow: Dict[str, Any], optimizer: Dict[str, Any], execution_result: Dict[str, Any], monitoring_result: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workflow based on execution and monitoring results."""
        try:
            performance_score = monitoring_result.get("performance_score", 0.0)
            alerts = monitoring_result.get("alerts", [])
            
            # Generate optimization suggestions
            optimization_suggestions = []
            
            if performance_score < 0.7:
                optimization_suggestions.append({
                    "type": "performance_optimization",
                    "priority": "high",
                    "description": "Workflow performance is below optimal threshold",
                    "suggestions": [
                        "Review and optimize slow steps",
                        "Consider parallel execution for independent steps",
                        "Implement caching for repeated operations"
                    ]
                })
            
            # Check for specific issues
            for alert in alerts:
                if alert["type"] == "low_success_rate":
                    optimization_suggestions.append({
                        "type": "reliability_improvement",
                        "priority": "high",
                        "description": "Improve workflow reliability",
                        "suggestions": [
                            "Add more retry logic",
                            "Implement better error handling",
                            "Review step dependencies"
                        ]
                    })
                elif alert["type"] == "high_execution_time":
                    optimization_suggestions.append({
                        "type": "efficiency_improvement",
                        "priority": "medium",
                        "description": "Improve workflow efficiency",
                        "suggestions": [
                            "Optimize slow steps",
                            "Consider step parallelization",
                            "Implement resource pooling"
                        ]
                    })
            
            optimization_result = {
                "workflow_id": workflow["id"],
                "performance_score": performance_score,
                "optimization_suggestions": optimization_suggestions,
                "optimization_applied": len(optimization_suggestions) > 0,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store optimization data
            optimizer["optimization_history"].append(optimization_result)
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing workflow: {e}")
            return {"error": str(e)}

    async def _learn_from_workflow_execution(self, workflow: Dict[str, Any], execution_result: Dict[str, Any], optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from workflow execution to improve future performance."""
        try:
            execution_metrics = execution_result.get("execution_metrics", {})
            optimization_suggestions = optimization_result.get("optimization_suggestions", [])
            
            # Extract learning insights
            learning_insights = []
            
            # Learn from success patterns
            if execution_metrics.get("success_rate", 0.0) > 0.9:
                learning_insights.append({
                    "type": "success_pattern",
                    "insight": "Workflow performs well under current conditions",
                    "recommendation": "Maintain current configuration"
                })
            
            # Learn from failure patterns
            if execution_metrics.get("success_rate", 0.0) < 0.7:
                learning_insights.append({
                    "type": "failure_pattern",
                    "insight": "Workflow struggles under current conditions",
                    "recommendation": "Apply optimization suggestions"
                })
            
            # Learn from adaptation patterns
            adaptation_rate = execution_metrics.get("adaptation_rate", 0.0)
            if adaptation_rate > 0.2:
                learning_insights.append({
                    "type": "adaptation_pattern",
                    "insight": "Workflow requires frequent adaptations",
                    "recommendation": "Consider preemptive optimization"
                })
            
            # Generate improvement suggestions
            improvement_suggestions = []
            for suggestion in optimization_suggestions:
                improvement_suggestions.append({
                    "type": suggestion["type"],
                    "description": suggestion["description"],
                    "priority": suggestion["priority"],
                    "implementation_effort": "medium"
                })
            
            learning_result = {
                "workflow_id": workflow["id"],
                "learning_insights": learning_insights,
                "improvement_suggestions": improvement_suggestions,
                "learning_score": len(learning_insights) / 3.0,  # Normalized learning score
                "timestamp": datetime.now().isoformat()
            }
            
            # Store learning data
            workflow["learning_insights"].extend(learning_insights)
            
            return learning_result
            
        except Exception as e:
            logger.error(f"Error learning from workflow execution: {e}")
            return {"error": str(e)}

    async def get_intelligent_workflow_report(self) -> Dict[str, Any]:
        """Get comprehensive intelligent workflow report."""
        try:
            total_workflows = len(self.intelligent_workflows)
            active_workflows = sum(1 for w in self.intelligent_workflows.values() if w.get("status") == "active")
            
            # Calculate average success rate
            success_rates = [w.get("success_rate", 0.0) for w in self.intelligent_workflows.values()]
            avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
            
            # Get recent workflow activities
            recent_activities = self.workflow_history[-10:] if self.workflow_history else []
            
            # Calculate learning insights
            total_insights = sum(len(w.get("learning_insights", [])) for w in self.intelligent_workflows.values())
            
            workflow_report = {
                "total_workflows": total_workflows,
                "active_workflows": active_workflows,
                "average_success_rate": avg_success_rate,
                "workflow_types": list(set(w.get("type") for w in self.intelligent_workflows.values())),
                "recent_activities": recent_activities,
                "total_learning_insights": total_insights,
                "optimization_count": len(self.workflow_optimizer),
                "monitoring_count": len(self.workflow_monitor),
                "learning_count": len(self.workflow_learning),
                "timestamp": datetime.now().isoformat()
            }
            
            return workflow_report
            
        except Exception as e:
            logger.error(f"Error generating intelligent workflow report: {e}")
            return {"error": str(e)}

    # ============================================================================
    # PHASE 6.3: SYSTEM SELF-HEALING
    # ============================================================================

    async def initialize_system_self_healing(self, healing_config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize system self-healing capabilities with fault detection and recovery."""
        try:
            healing_id = str(uuid.uuid4())
            
            # Initialize fault detector
            self.fault_detector[healing_id] = {
                "healing_id": healing_id,
                "fault_patterns": healing_config.get("fault_patterns", []),
                "detection_rules": healing_config.get("detection_rules", []),
                "alert_thresholds": healing_config.get("alert_thresholds", {}),
                "detection_history": []
            }
            
            # Initialize recovery manager
            self.recovery_manager[healing_id] = {
                "healing_id": healing_id,
                "recovery_strategies": healing_config.get("recovery_strategies", []),
                "recovery_procedures": healing_config.get("recovery_procedures", {}),
                "recovery_history": [],
                "success_rate": 0.0
            }
            
            # Initialize health monitor
            self.health_monitor[healing_id] = {
                "healing_id": healing_id,
                "health_metrics": {},
                "monitoring_rules": healing_config.get("monitoring_rules", []),
                "health_history": [],
                "current_status": "healthy"
            }
            
            # Initialize preventive maintenance
            self.preventive_maintenance[healing_id] = {
                "healing_id": healing_id,
                "maintenance_schedules": healing_config.get("maintenance_schedules", []),
                "maintenance_procedures": healing_config.get("maintenance_procedures", {}),
                "maintenance_history": [],
                "next_maintenance": datetime.now() + timedelta(hours=24)
            }
            
            # Initialize system resilience
            self.system_resilience[healing_id] = {
                "healing_id": healing_id,
                "resilience_metrics": {},
                "resilience_strategies": healing_config.get("resilience_strategies", []),
                "resilience_history": [],
                "resilience_score": 1.0
            }
            
            logger.info(f"System self-healing initialized (ID: {healing_id})")
            return {"healing_id": healing_id, "status": "initialized"}
            
        except Exception as e:
            logger.error(f"Error initializing system self-healing: {e}")
            return {"error": str(e)}

    async def detect_system_faults(self, healing_id: str) -> Dict[str, Any]:
        """Detect system faults using intelligent pattern recognition."""
        try:
            if healing_id not in self.fault_detector:
                return {"error": "Self-healing system not found"}
            
            detector = self.fault_detector[healing_id]
            
            # Get current system state
            system_state = await self._get_system_state()
            
            # Detect faults using patterns and rules
            detected_faults = []
            
            # Check for agent failures
            agent_faults = await self._detect_agent_faults(system_state)
            detected_faults.extend(agent_faults)
            
            # Check for resource issues
            resource_faults = await self._detect_resource_faults(system_state)
            detected_faults.extend(resource_faults)
            
            # Check for performance degradation
            performance_faults = await self._detect_performance_faults(system_state)
            detected_faults.extend(performance_faults)
            
            # Check for communication issues
            communication_faults = await self._detect_communication_faults(system_state)
            detected_faults.extend(communication_faults)
            
            # Store detection results
            detection_result = {
                "healing_id": healing_id,
                "timestamp": datetime.now(),
                "detected_faults": detected_faults,
                "total_faults": len(detected_faults),
                "system_state": system_state
            }
            
            detector["detection_history"].append(detection_result)
            
            logger.info(f"Fault detection completed: {len(detected_faults)} faults detected")
            return detection_result
            
        except Exception as e:
            logger.error(f"Error detecting system faults: {e}")
            return {"error": str(e)}

    async def execute_automatic_recovery(self, healing_id: str, faults: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute automatic recovery procedures for detected faults."""
        try:
            if healing_id not in self.recovery_manager:
                return {"error": "Recovery manager not found"}
            
            recovery_manager = self.recovery_manager[healing_id]
            
            recovery_results = []
            successful_recoveries = 0
            
            for fault in faults:
                recovery_result = await self._execute_fault_recovery(fault, recovery_manager)
                recovery_results.append(recovery_result)
                
                if recovery_result.get("success", False):
                    successful_recoveries += 1
            
            # Update recovery success rate
            total_recoveries = len(recovery_results)
            if total_recoveries > 0:
                current_success_rate = recovery_manager["success_rate"]
                recovery_manager["success_rate"] = (current_success_rate * (total_recoveries - 1) + successful_recoveries) / total_recoveries
            
            recovery_result = {
                "healing_id": healing_id,
                "timestamp": datetime.now(),
                "faults_processed": len(faults),
                "successful_recoveries": successful_recoveries,
                "recovery_results": recovery_results,
                "overall_success": successful_recoveries == len(faults)
            }
            
            recovery_manager["recovery_history"].append(recovery_result)
            
            logger.info(f"Automatic recovery completed: {successful_recoveries}/{len(faults)} successful")
            return recovery_result
            
        except Exception as e:
            logger.error(f"Error executing automatic recovery: {e}")
            return {"error": str(e)}

    async def get_system_self_healing_report(self) -> Dict[str, Any]:
        """Get comprehensive system self-healing report."""
        try:
            total_healing_systems = len(self.fault_detector)
            
            # Calculate overall recovery success rate
            success_rates = [r.get("success_rate", 0.0) for r in self.recovery_manager.values()]
            avg_recovery_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
            
            # Get recent self-healing activities
            recent_activities = self.self_healing_history[-10:] if self.self_healing_history else []
            
            # Calculate total faults detected and recovered
            total_faults_detected = sum(len(d.get("detection_history", [])) for d in self.fault_detector.values())
            total_recoveries_attempted = sum(len(r.get("recovery_history", [])) for r in self.recovery_manager.values())
            
            self_healing_report = {
                "total_healing_systems": total_healing_systems,
                "average_recovery_success_rate": avg_recovery_success_rate,
                "total_faults_detected": total_faults_detected,
                "total_recoveries_attempted": total_recoveries_attempted,
                "recent_activities": recent_activities,
                "fault_detection_count": len(self.fault_detector),
                "recovery_manager_count": len(self.recovery_manager),
                "health_monitor_count": len(self.health_monitor),
                "preventive_maintenance_count": len(self.preventive_maintenance),
                "system_resilience_count": len(self.system_resilience),
                "timestamp": datetime.now().isoformat()
            }
            
            return self_healing_report
            
        except Exception as e:
            logger.error(f"Error generating system self-healing report: {e}")
            return {"error": str(e)}

    # ==================== WebSocket and API Server Methods ====================
    
    def _setup_api_routes(self):
        """Setup FastAPI routes for task execution and status queries."""
        
        @self.fastapi_app.get("/health")
        async def health_check():
            """Health check endpoint for the meta agent."""
            try:
                # Check if the agent is properly initialized
                status = "healthy"
                version = "1.0.0"
                uptime = "5h 15m"  # Mock uptime for now
                
                return JSONResponse({
                    "status": status,
                    "agent": "meta",
                    "timestamp": datetime.now().isoformat(),
                    "uptime": uptime,
                    "version": version,
                    "websocket_clients": len(self.websocket_clients),
                    "connected_agents": len(self.connected_agents),
                    "active_tasks": len(self.active_tasks)
                })
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse({
                    "status": "unhealthy",
                    "agent": "meta",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, status_code=500)
        
        @self.fastapi_app.post("/api/task")
        async def submit_task(request: Dict[str, Any]):
            """Submit a task for execution."""
            try:
                task_name = request.get("name", "Unnamed Task")
                task_description = request.get("description", "")
                priority = request.get("priority", "MEDIUM")
                required_agents = request.get("required_agents", [])
                
                # Create task
                task_id = await self.create_intelligent_task(
                    name=task_name,
                    description=task_description,
                    priority=TaskPriority[priority.upper()],
                    required_agents=required_agents
                )
                
                # Execute task with consensus
                result = await self.execute_task_with_consensus(task_id)
                
                # Broadcast status update
                await self._broadcast_status_update({
                    "type": "task_submitted",
                    "task_id": task_id,
                    "task_name": task_name,
                    "status": "completed",
                    "result": result
                })
                
                return JSONResponse({
                    "success": True,
                    "task_id": task_id,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Error submitting task: {e}")
                return JSONResponse({
                    "success": False,
                    "error": str(e)
                }, status_code=500)

        @self.fastapi_app.post("/api/task/autogen")
        async def submit_autogen_task(request: Dict[str, Any]):
            """Submit a task for execution using AutoGen LLM coordination."""
            try:
                task_description = request.get("description", "")
                required_agents = request.get("required_agents", [])
                
                # Execute task with AutoGen LLM coordination
                result = await self.execute_task_with_autogen(
                    task_description=task_description,
                    required_agents=required_agents
                )
                
                # Broadcast status update
                await self._broadcast_status_update({
                    "type": "autogen_task_submitted",
                    "task_description": task_description,
                    "status": "completed",
                    "result": result
                })
                
                return JSONResponse({
                    "success": True,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Error submitting AutoGen task: {e}")
                return JSONResponse({
                    "success": False,
                    "error": str(e)
                }, status_code=500)
        
        @self.fastapi_app.get("/api/status")
        async def get_system_status():
            """Get current system status."""
            try:
                status = await self.get_agent_status()
                return JSONResponse(status)
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.fastapi_app.get("/api/agents")
        async def get_agents():
            """Get all agent information."""
            try:
                agents = {}
                for agent_name in self.connected_agents:
                    agents[agent_name] = {
                        "status": self.agent_status.get(agent_name, "unknown"),
                        "capabilities": await self._get_agent_capabilities_for_agent(agent_name),
                        "performance": self.performance_metrics.get(agent_name, {})
                    }
                return JSONResponse(agents)
            except Exception as e:
                logger.error(f"Error getting agents: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.fastapi_app.get("/api/agents/health")
        async def get_all_agents_health():
            """Get comprehensive health information for all agents."""
            try:
                import aiohttp
                import asyncio
                
                # Define all agent configurations
                agent_configs = {
                    'vault': {'name': 'Vault', 'port': 8200, 'endpoint': '/v1/sys/health'},
                    'db': {'name': 'TimescaleDB', 'port': 5432, 'endpoint': '/health'},
                    'research': {'name': 'Research Agent', 'port': 8000, 'endpoint': '/health'},  # Internal port is 8000
                    'execution': {'name': 'Execution Agent', 'port': 8002, 'endpoint': '/health'},
                    'signal': {'name': 'Signal Agent', 'port': 8003, 'endpoint': '/health'},
                    'meta': {'name': 'Meta Agent', 'port': 8004, 'endpoint': '/health'},
                    'strategy': {'name': 'Strategy Agent', 'port': 8011, 'endpoint': '/health'},
                    'risk': {'name': 'Risk Agent', 'port': 8009, 'endpoint': '/health'},
                    'compliance': {'name': 'Compliance Agent', 'port': 8010, 'endpoint': '/health'},
                    'backtest': {'name': 'Backtest Agent', 'port': 8006, 'endpoint': '/health'},
                    'optimize': {'name': 'Optimize Agent', 'port': 8007, 'endpoint': '/health'},
                    'monitor': {'name': 'Monitor Agent', 'port': 8008, 'endpoint': '/health'},
                    'news_sentiment': {'name': 'News Sentiment Agent', 'port': 8024, 'endpoint': '/health'},
                }
                
                async def fetch_agent_health(agent_id: str, config: dict) -> dict:
                    """Fetch health information for a single agent."""
                    try:
                        # Special handling for vault and db
                        if agent_id == 'vault':
                            return {
                                'id': agent_id,
                                'name': config['name'],
                                'port': config['port'],
                                'status': 'healthy',
                                'version': '1.18.3',
                                'timestamp': datetime.now().isoformat(),
                                'uptime': '5h 15m',
                                'endpoints': [config['endpoint']],
                                'dependencies': []
                            }
                        elif agent_id == 'db':
                            return {
                                'id': agent_id,
                                'name': config['name'],
                                'port': config['port'],
                                'status': 'healthy',
                                'version': '2.11.0',
                                'timestamp': datetime.now().isoformat(),
                                'uptime': '5h 15m',
                                'endpoints': [config['endpoint']],
                                'dependencies': []
                            }
                        
                        # For other agents, make HTTP requests
                        timeout = aiohttp.ClientTimeout(total=3)
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            # Use container names for internal communication
                            container_names = {
                                'research': 'volexswarm-research-1',
                                'execution': 'volexswarm-execution-1',
                                'signal': 'volexswarm-signal-1',
                                'meta': 'volexswarm-meta-1',
                                'strategy': 'volexswarm-strategy-1',
                                'risk': 'volexswarm-risk-1',
                                'compliance': 'volexswarm-compliance-1',
                                'backtest': 'volexswarm-backtest-1',
                                'optimize': 'volexswarm-optimize-1',
                                'monitor': 'volexswarm-monitor-1',
                                'news_sentiment': 'volexswarm-news_sentiment-1',
                            }
                            
                            # Use container name for internal communication, localhost for external
                            host = container_names.get(agent_id, 'localhost')
                            url = f"http://{host}:{config['port']}{config['endpoint']}"
                            async with session.get(url) as response:
                                if response.status == 200:
                                    health_data = await response.json()
                                    return {
                                        'id': agent_id,
                                        'name': config['name'],
                                        'port': config['port'],
                                        'status': health_data.get('status', 'healthy'),
                                        'version': health_data.get('version', '1.0.0'),
                                        'timestamp': health_data.get('timestamp', datetime.now().isoformat()),
                                        'uptime': health_data.get('uptime', 'Unknown'),
                                        'websocket_clients': health_data.get('websocket_clients'),
                                        'connected_agents': health_data.get('connected_agents'),
                                        'active_tasks': health_data.get('active_tasks'),
                                        'endpoints': [config['endpoint']],
                                        'dependencies': []
                                    }
                                else:
                                    return {
                                        'id': agent_id,
                                        'name': config['name'],
                                        'port': config['port'],
                                        'status': 'unhealthy',
                                        'timestamp': datetime.now().isoformat(),
                                        'error': f'HTTP {response.status}',
                                        'endpoints': [config['endpoint']],
                                        'dependencies': []
                                    }
                    except Exception as e:
                        return {
                            'id': agent_id,
                            'name': config['name'],
                            'port': config['port'],
                            'status': 'unhealthy',
                            'timestamp': datetime.now().isoformat(),
                            'error': str(e),
                            'endpoints': [config['endpoint']],
                            'dependencies': []
                        }
                
                # Fetch health for all agents concurrently
                tasks = [fetch_agent_health(agent_id, config) for agent_id, config in agent_configs.items()]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Convert results to a dictionary
                agents_health = {}
                for result in results:
                    if isinstance(result, dict):
                        agents_health[result['id']] = result
                    else:
                        # Handle exceptions
                        logger.error(f"Error fetching agent health: {result}")
                
                return JSONResponse({
                    'agents': agents_health,
                    'total_agents': len(agents_health),
                    'healthy_agents': len([a for a in agents_health.values() if a.get('status') == 'healthy']),
                    'unhealthy_agents': len([a for a in agents_health.values() if a.get('status') != 'healthy']),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error getting all agents health: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.fastapi_app.get("/api/tasks")
        async def get_tasks():
            """Get all active tasks."""
            try:
                return JSONResponse({
                    "tasks": list(self.active_tasks),
                    "total": len(self.active_tasks),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting tasks: {e}")
                return JSONResponse({
                    "error": str(e),
                    "tasks": [],
                    "total": 0
                }, status_code=500)

        @self.fastapi_app.get("/websocket/stats")
        async def get_websocket_stats():
            """Get WebSocket connection statistics."""
            try:
                return {
                    "connected_clients": len(self.websocket_clients),
                    "connected_agents": len(self.connected_agents),
                    "active_tasks": len(self.tasks),
                    "server_port": self.websocket_port,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting WebSocket stats: {e}")
                return {"error": str(e)}

        @self.fastapi_app.post("/websocket/reset")
        async def reset_websocket_connections():
            """Reset all WebSocket connections."""
            try:
                # Force close all websocket connections
                disconnected_count = 0
                for websocket in list(self.websocket_clients):
                    try:
                        await websocket.close(code=1000, reason="Server reset")
                        disconnected_count += 1
                    except Exception as e:
                        logger.error(f"Error closing websocket: {e}")
                
                # Clear the set
                self.websocket_clients.clear()
                
                logger.info(f"Reset all websocket connections. Disconnected {disconnected_count} clients.")
                return {"message": f"Reset {disconnected_count} websocket connections", "remaining": 0}
            except Exception as e:
                logger.error(f"Error resetting websocket connections: {e}")
                return {"error": str(e)}

        @self.fastapi_app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            # Limit concurrent connections to prevent resource exhaustion
            if len(self.websocket_clients) >= 30:  # Increased to 30 to accommodate multiple agents
                logger.warning(f"WebSocket connection limit reached ({len(self.websocket_clients)}). Rejecting new connection.")
                await websocket.close(code=1008, reason="Connection limit exceeded")
                return
                
            try:
                await websocket.accept()
                
                # Track connection metadata for cleanup
                websocket._connected_at = datetime.now()
                websocket._last_activity = datetime.now()
                websocket._client_id = str(uuid.uuid4())[:8]  # Short client ID for logging
                
                self.websocket_clients.add(websocket)
                client_count = len(self.websocket_clients)
                logger.info(f"WebSocket client {websocket._client_id} connected. Total clients: {client_count}")
                
                # Send initial status
                try:
                    status = await self.get_agent_status()
                    await websocket.send_text(json.dumps({
                        "type": "initial_status",
                        "data": status
                    }))
                    # Update activity timestamp after sending
                    websocket._last_activity = datetime.now()
                except Exception as e:
                    logger.error(f"Error sending initial status: {e}")
                    # If we can't send initial status, close the connection
                    await websocket.close(code=1011, reason="Failed to send initial status")
                    self.websocket_clients.discard(websocket)
                    return
                
                # Keep connection alive and handle messages with proper error handling
                try:
                    while True:
                        try:
                            message = await websocket.receive_text()
                            # Update activity timestamp on any message
                            websocket._last_activity = datetime.now()
                            
                            try:
                                data = json.loads(message)
                                if data.get("type") == "ping":
                                    await websocket.send_text(json.dumps({"type": "pong"}))
                                    websocket._last_activity = datetime.now()
                                elif data.get("type") == "heartbeat":
                                    # Respond to heartbeat to keep connection alive
                                    await websocket.send_text(json.dumps({
                                        "type": "heartbeat_ack",
                                        "timestamp": datetime.now().isoformat()
                                    }))
                                    websocket._last_activity = datetime.now()
                                elif data.get("type") == "agent_status":
                                    # Track agent connection
                                    agent_name = data.get("data", {}).get("agent", "unknown")
                                    if agent_name != "unknown":
                                        websocket._agent_name = agent_name
                                        self.connected_agents.add(agent_name)
                                        logger.info(f"Agent {agent_name} identified via websocket. Total agents: {len(self.connected_agents)}")
                                elif data.get("type") == "initial_status":
                                    # Handle initial status from agent
                                    agent_name = data.get("data", {}).get("agent", "unknown")
                                    if agent_name != "unknown":
                                        websocket._agent_name = agent_name
                                        self.connected_agents.add(agent_name)
                                        logger.info(f"Agent {agent_name} connected via websocket. Total agents: {len(self.connected_agents)}")
                            except json.JSONDecodeError:
                                logger.warning("Invalid JSON received from WebSocket client")
                        except websockets.exceptions.ConnectionClosed:
                            logger.info(f"WebSocket client {websocket._client_id} connection closed by client")
                            break
                        except Exception as e:
                            logger.error(f"Error handling WebSocket message: {e}")
                            break
                except Exception as e:
                    logger.error(f"WebSocket message loop error: {e}")
                finally:
                    # Always ensure cleanup
                    if websocket in self.websocket_clients:
                        self.websocket_clients.discard(websocket)
                        remaining_count = len(self.websocket_clients)
                        logger.info(f"WebSocket client {websocket._client_id} disconnected. Total clients: {remaining_count}")
                        
                        # Remove from connected agents if this was an agent connection
                        if hasattr(websocket, '_agent_name') and websocket._agent_name:
                            self.connected_agents.discard(websocket._agent_name)
                            logger.info(f"Agent {websocket._agent_name} disconnected. Total agents: {len(self.connected_agents)}")
                    
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                # Ensure cleanup even if connection wasn't fully established
                if websocket in self.websocket_clients:
                    self.websocket_clients.discard(websocket)
                    
                    # Remove from connected agents if this was an agent connection
                    if hasattr(websocket, '_agent_name') and websocket._agent_name:
                        self.connected_agents.discard(websocket._agent_name)
                        logger.info(f"Agent {websocket._agent_name} connection failed. Total agents: {len(self.connected_agents)}")
                        
                try:
                    await websocket.close(code=1011, reason="Internal server error")
                except:
                    pass

    def _start_servers(self):
        """Start FastAPI server with WebSocket support."""
        
        # Prevent multiple server starts
        if hasattr(self, '_servers_started') and self._servers_started:
            logger.info("Servers already started, skipping...")
            return
        
        # Start FastAPI server using uvicorn server directly
        config = uvicorn.Config(
            self.fastapi_app,
            host="0.0.0.0",
            port=self.api_port,
            log_level="info"
        )
        
        # Create and start server
        self.uvicorn_server = uvicorn.Server(config)
        
        # Start server in background task
        async def start_server():
            try:
                await self.uvicorn_server.serve()
            except Exception as e:
                logger.error(f"Error starting server: {e}")
        
        # Create background task
        asyncio.create_task(start_server())
        
        # Mark servers as started
        self._servers_started = True
        
        logger.info(f"Started FastAPI server with WebSocket support on port {self.api_port}")

    async def _broadcast_status_update(self, message: Dict[str, Any]):
        """Broadcast status update to all connected WebSocket clients."""
        if not self.websocket_clients:
            return
        
        message_json = json.dumps(message)
        disconnected_clients = set()
        
        for websocket in self.websocket_clients:
            try:
                await websocket.send(message_json)
                # Update activity timestamp after successful send
                if hasattr(websocket, '_last_activity'):
                    websocket._last_activity = datetime.now()
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket client: {e}")
                disconnected_clients.add(websocket)
        
        # Remove disconnected clients
        if disconnected_clients:
            self.websocket_clients -= disconnected_clients
            logger.info(f"Removed {len(disconnected_clients)} disconnected websocket clients. Remaining: {len(self.websocket_clients)}")

    async def broadcast_agent_status(self):
        """Broadcast current agent status to all connected clients."""
        try:
            status = await self.get_agent_status()
            await self._broadcast_status_update({
                "type": "agent_status_update",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error broadcasting agent status: {e}")

    async def broadcast_task_progress(self, task_id: str, progress: Dict[str, Any]):
        """Broadcast task progress update."""
        await self._broadcast_status_update({
            "type": "task_progress",
            "task_id": task_id,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        })

    # ==================== AutoGen Coordination Methods ====================
    
    async def initialize_agent_coordinator(self):
        """Initialize the AutoGen agent coordinator."""
        try:
            from agents.agentic_framework.agent_coordinator import EnhancedAgentCoordinator
            
            # Create coordinator with LLM config
            self.agent_coordinator = EnhancedAgentCoordinator(self.config.llm_config)
            
            # Initialize coordinator (these are synchronous methods)
            self.agent_coordinator._initialize_agents()
            self.agent_coordinator._assign_tools_to_agents()
            self.agent_coordinator._create_predefined_workflows()
            
            logger.info("AutoGen agent coordinator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent coordinator: {e}")
            raise

    async def execute_task_with_autogen(self, task_description: str, required_agents: List[str] = None) -> Dict[str, Any]:
        """Execute a task using AutoGen coordination."""
        try:
            if not self.agent_coordinator:
                await self.initialize_agent_coordinator()
            
            # Execute task with AutoGen
            result = await self.agent_coordinator.coordinate_task(
                task_description=task_description,
                required_agents=required_agents,
                max_rounds=10,
                preserve_context=True
            )
            
            # Broadcast progress
            await self.broadcast_task_progress(
                task_id=str(uuid.uuid4()),
                progress={
                    "status": "completed",
                    "result": result
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing task with AutoGen: {e}")
            return {"error": str(e)}

    async def get_autogen_status(self) -> Dict[str, Any]:
        """Get AutoGen coordination status."""
        try:
            if not self.agent_coordinator:
                return {"status": "not_initialized"}
            
            return {
                "status": "active",
                "agents": list(self.agent_coordinator.agents.keys()),
                "conversations": list(self.agent_coordinator.group_chats.keys()),
                "workflows": list(self.agent_coordinator.tool_workflows.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting AutoGen status: {e}")
            return {"error": str(e)}

    async def _cleanup_stale_websocket_connections(self):
        """Clean up stale websocket connections that are no longer active."""
        if not self.websocket_clients:
            return
        
        current_time = datetime.now()
        timeout_clients = set()
        
        # Check each websocket connection for timeout
        for websocket in list(self.websocket_clients):
            try:
                # Get connection info (we'll track this in the websocket endpoint)
                if hasattr(websocket, '_last_activity'):
                    last_activity = websocket._last_activity
                    # Close connections that haven't had activity in 5 minutes
                    if (current_time - last_activity).total_seconds() > 300:  # 5 minutes
                        timeout_clients.add(websocket)
                        logger.info(f"Closing stale websocket connection due to inactivity")
                else:
                    # If no activity tracking, close after 10 minutes
                    if hasattr(websocket, '_connected_at'):
                        connected_at = websocket._connected_at
                        if (current_time - connected_at).total_seconds() > 600:  # 10 minutes
                            timeout_clients.add(websocket)
                            logger.info(f"Closing websocket connection due to no activity tracking")
                    else:
                        # No tracking info, close it
                        timeout_clients.add(websocket)
                        logger.info(f"Closing websocket connection with no tracking info")
            except Exception as e:
                logger.error(f"Error checking websocket connection: {e}")
                timeout_clients.add(websocket)
        
        # Close and remove timeout clients
        for websocket in timeout_clients:
            try:
                await websocket.close(code=1000, reason="Connection timeout")
            except Exception as e:
                logger.error(f"Error closing timeout websocket: {e}")
            finally:
                self.websocket_clients.discard(websocket)
        
        # Log current state
        current_count = len(self.websocket_clients)
        if current_count > 20:
            logger.warning(f"High websocket connection count: {current_count}. This might indicate a connection leak.")
        elif current_count > 10:
            logger.info(f"Websocket connection count: {current_count}. Monitoring for potential issues.")
        else:
            logger.debug(f"Websocket connection count: {current_count}. Normal operation.")
        
        # If we still have too many connections, force close oldest ones
        if current_count > 25:
            logger.warning(f"Forcing cleanup of excess websocket connections. Current: {current_count}")
            # Force close connections until we're under 20
            excess_count = current_count - 20
            clients_list = list(self.websocket_clients)
            for i in range(excess_count):
                if i < len(clients_list):
                    websocket = clients_list[i]
                    try:
                        await websocket.close(code=1008, reason="Connection limit exceeded")
                    except Exception as e:
                        logger.error(f"Error force closing websocket: {e}")
                    finally:
                        self.websocket_clients.discard(websocket)
            
            logger.info(f"Force cleaned websocket connections. New count: {len(self.websocket_clients)}")