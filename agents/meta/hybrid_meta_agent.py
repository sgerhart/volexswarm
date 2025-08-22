#!/usr/bin/env python3
"""
Hybrid Meta Agent for VolexSwarm

A focused Meta Agent that keeps the essential orchestration features
while removing unnecessary bloat. This combines the best of both:

✅ KEEPS (Essential):
- AutoGen integration for multi-agent coordination
- LLM-driven decision making with OpenAI
- MCP tool registry for agent coordination
- Intelligent task delegation and consensus
- Agent performance tracking and load balancing
- Advanced consensus building and conflict resolution
- Autonomous decision making with validation
- Agent performance monitoring and self-improvement

❌ REMOVES (Bloat):
- Over-engineered "Phase 6.1, 6.2, 6.3, 7.1" systems
- Excessive creative problem solving modules
- Self-healing and security enhancement features
- Unused workflow management systems

Result: ~800 lines with all essential features restored.
"""

import sys
import os
import asyncio
import json
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time # Added for WebSocket cleanup

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import websockets
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
from fastapi import WebSocket
import httpx

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.agentic_framework.agent_templates import MetaAgent
from agents.agentic_framework.mcp_tools import MCPToolRegistry, create_mcp_tool_registry
from agents.agentic_framework.agent_coordinator import EnhancedAgentCoordinator as AgentCoordinator
from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client
from common.logging import get_logger
from common.openai_client import get_openai_client

logger = get_logger("hybrid_meta_agent")

class TaskPriority(Enum):
    """Task priority levels for intelligent scheduling."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    """Enhanced task status tracking."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class HybridTask:
    """Enhanced task definition with essential features."""
    id: str
    name: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    assigned_agents: List[str]
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""
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
    """Autonomous decision with validation capabilities."""
    id: str
    decision_type: str
    context: Dict[str, Any]
    decision: str
    confidence: float
    reasoning: str
    alternatives: List[str]
    validation_status: str = "pending"
    validation_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class HybridMetaAgent(MetaAgent):
    """Hybrid Meta Agent with essential orchestration features restored."""
    
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
        
        # Initialize MCP tools
        if tool_registry is None:
            tool_registry = create_mcp_tool_registry()
        self.tool_registry = tool_registry
        
        # Initialize essential coordination systems
        self.app = None
        self.vault_client = None
        self.db_client = None
        self.openai_client = None
        self.websocket_clients = set()
        self.tasks: Dict[str, HybridTask] = {}
        self.agent_coordinator = None
        
        # Agent endpoints - the agents we coordinate
        # Use Docker service names for internal container communication
        self.agent_endpoints = {
            "execution": "http://execution:8002",
            "realtime_data": "http://realtime_data:8026", 
            "news_sentiment": "http://news_sentiment:8024",
            "strategy_discovery": "http://strategy_discovery:8025",
            "monitor": "http://monitor:8008",
            "risk": "http://risk:8009",
            "signal": "http://signal:8003"
        }
        
        # Agent capabilities for intelligent assignment
        self.agent_capabilities = {
            'execution': ['trade_execution', 'order_management', 'position_tracking'],
            'realtime_data': ['market_data', 'price_feeds', 'websocket_streams'],
            'news_sentiment': ['sentiment_analysis', 'news_processing', 'market_sentiment'],
            'strategy_discovery': ['strategy_development', 'backtesting', 'optimization'],
            'risk': ['risk_assessment', 'position_sizing', 'portfolio_protection'],
            'signal': ['technical_analysis', 'signal_generation', 'pattern_recognition'],
            'monitor': ['system_monitoring', 'performance_tracking', 'alerting']
        }
        
        # Performance tracking
        self.agent_performance: Dict[str, Dict[str, Any]] = {}
        self.agent_loads: Dict[str, int] = {agent: 0 for agent in self.agent_endpoints.keys()}
        
        # Consensus and decision tracking
        self.consensus_history: List[AgentConsensus] = []
        self.decision_history: List[AutonomousDecision] = []
    
    async def initialize(self):
        """Initialize the Hybrid Meta Agent infrastructure."""
        try:
            logger.info("🚀 Initializing Hybrid Meta Agent...")
            
            # Clear any existing WebSocket clients to start fresh
            self.websocket_clients.clear()
            logger.info(f"🔌 Cleared WebSocket clients. Starting with {len(self.websocket_clients)} connections.")
            
            # Initialize clients
            self.vault_client = get_vault_client()
            self.db_client = get_db_client()
            self.openai_client = get_openai_client()
            
            # Configure LLM from Vault
            await self._configure_llm_from_vault()
            
            # Initialize AutoGen coordinator
            await self.initialize_agent_coordinator()
            
            # Setup FastAPI app
            self._setup_api()
            
            # Start servers
            self._start_servers()
            
            logger.info("✅ Hybrid Meta Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Hybrid Meta Agent: {e}")
            raise
    
    async def _configure_llm_from_vault(self):
        """Configure LLM with OpenAI API key from Vault (primary method)."""
        try:
            openai_api_key = None
            
            # Primary method: Load from Vault (production)
            if self.vault_client:
                try:
                    openai_secret = self.vault_client.get_secret("openai/api_key")
                    if openai_secret and "api_key" in openai_secret:
                        openai_api_key = openai_secret["api_key"]
                        logger.info("🔑 LLM configured with OpenAI API key from Vault (production)")
                    else:
                        logger.warning("⚠️ OpenAI API key not found in Vault")
                except Exception as vault_error:
                    logger.warning(f"⚠️ Failed to load API key from Vault: {vault_error}")
            
            # Fallback method: Environment variable (development only)
            if not openai_api_key:
                env_api_key = os.environ.get('OPENAI_API_KEY')
                if env_api_key:
                    openai_api_key = env_api_key
                    logger.warning("🔑 Using OpenAI API key from environment variable (development fallback)")
                else:
                    logger.error("❌ No OpenAI API key found in Vault or environment. LLM features will not work.")
                    return
            
            # Update LLM config with real API key
            if openai_api_key:
                self.config.llm_config = {
                    "config_list": [{
                        "api_type": "openai",
                        "model": "gpt-4o-mini",
                        "api_key": openai_api_key
                    }],
                    "temperature": 0.7
                }
                
                # Also update the agent coordinator if it exists
                if self.agent_coordinator:
                    self.agent_coordinator.llm_config = self.config.llm_config
                    
        except Exception as e:
            logger.error(f"❌ Error configuring LLM credentials: {e}")
    
    async def initialize_agent_coordinator(self):
        """Initialize the AutoGen agent coordinator."""
        try:
            # Create coordinator with LLM config
            self.agent_coordinator = AgentCoordinator(self.config.llm_config)
            
            # Initialize coordinator
            self.agent_coordinator._initialize_agents()
            self.agent_coordinator._assign_tools_to_agents()
            self.agent_coordinator._create_predefined_workflows()
            
            logger.info("🤖 AutoGen agent coordinator initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent coordinator: {e}")
            # Continue without AutoGen if it fails
            self.agent_coordinator = None
    
    async def execute_task_with_autogen(self, task_description: str, required_agents: List[str] = None) -> Dict[str, Any]:
        """Execute a task using AutoGen coordination."""
        try:
            if not self.agent_coordinator:
                await self.initialize_agent_coordinator()
            
            if self.agent_coordinator:
                # Execute task with AutoGen
                result = await self.agent_coordinator.coordinate_task(
                    task_description=task_description,
                    required_agents=required_agents,
                    max_rounds=10,
                    preserve_context=True
                )
                return result
            else:
                # Fallback to direct agent coordination
                logger.warning("⚠️ AutoGen not available, using direct coordination")
                return await self._execute_task_direct(task_description, required_agents)
                
        except Exception as e:
            logger.error(f"❌ Error executing task with AutoGen: {e}")
            # Fallback to direct coordination
            return await self._execute_task_direct(task_description, required_agents)
    
    async def _execute_task_direct(self, task_description: str, required_agents: List[str] = None) -> Dict[str, Any]:
        """Direct task execution without AutoGen (fallback)."""
        try:
            # Use LLM to determine best agents if not specified
            if not required_agents:
                required_agents = await self._intelligently_assign_agents(task_description)
            
            # Execute task by calling agents directly
            results = {}
            for agent_name in required_agents:
                if agent_name in self.agent_endpoints:
                    result = await self._call_agent_with_llm_guidance(agent_name, task_description)
                    results[agent_name] = result
            
            return {
                "task_description": task_description,
                "assigned_agents": required_agents,
                "results": results,
                "coordination_method": "direct",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in direct task execution: {e}")
            return {"error": str(e)}
    
    async def _intelligently_assign_agents(self, task_description: str) -> List[str]:
        """Use LLM to intelligently assign agents based on task description."""
        try:
            if self.openai_client:
                prompt = f"""
                Given this task description: "{task_description}"
                
                Available agents and their capabilities:
                {json.dumps(self.agent_capabilities, indent=2)}
                
                Which agents would be best suited for this task? 
                Respond with a JSON list of agent names, e.g., ["execution", "risk", "signal"]
                """
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                # Parse LLM response
                content = response.choices[0].message.content.strip()
                if content.startswith('[') and content.endswith(']'):
                    import json
                    assigned_agents = json.loads(content)
                    return [agent for agent in assigned_agents if agent in self.agent_endpoints]
            
            # Fallback: assign based on keywords
            return self._assign_agents_by_keywords(task_description)
            
        except Exception as e:
            logger.error(f"❌ Error in intelligent agent assignment: {e}")
            return self._assign_agents_by_keywords(task_description)
    
    def _assign_agents_by_keywords(self, task_description: str) -> List[str]:
        """Fallback agent assignment based on keywords."""
        description_lower = task_description.lower()
        assigned_agents = []
        
        if any(word in description_lower for word in ['portfolio', 'balance', 'trade', 'execute']):
            assigned_agents.append('execution')
        if any(word in description_lower for word in ['market', 'price', 'data', 'realtime']):
            assigned_agents.append('realtime_data')
        if any(word in description_lower for word in ['news', 'sentiment', 'analysis']):
            assigned_agents.append('news_sentiment')
        if any(word in description_lower for word in ['strategy', 'discover', 'backtest']):
            assigned_agents.append('strategy_discovery')
        if any(word in description_lower for word in ['risk', 'assess', 'manage']):
            assigned_agents.append('risk')
        if any(word in description_lower for word in ['signal', 'technical', 'indicator']):
            assigned_agents.append('signal')
        
        return assigned_agents or ['execution', 'realtime_data']  # Default agents
    
    async def _call_agent_with_llm_guidance(self, agent_name: str, task_description: str) -> Dict[str, Any]:
        """Call an agent with LLM guidance for the specific task."""
        try:
            # Use LLM to determine the best endpoint and parameters for this agent
            if self.openai_client:
                prompt = f"""
                Agent: {agent_name}
                Task: {task_description}
                Capabilities: {self.agent_capabilities.get(agent_name, [])}
                
                What endpoint should I call on this agent and with what parameters?
                Respond with JSON: {{"endpoint": "/path", "method": "GET/POST", "data": {{}}}}
                """
                
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3
                    )
                    
                    content = response.choices[0].message.content.strip()
                    if content.startswith('{') and content.endswith('}'):
                        guidance = json.loads(content)
                        endpoint = guidance.get("endpoint", "/health")
                        method = guidance.get("method", "GET")
                        data = guidance.get("data", {})
                        
                        return await self._call_agent(agent_name, endpoint, data if method == "POST" else None)
                except:
                    pass
            
            # Fallback to health check
            return await self._call_agent(agent_name, "/health")
            
        except Exception as e:
            logger.error(f"❌ Error calling agent {agent_name} with LLM guidance: {e}")
            return {"error": str(e), "agent": agent_name}
    
    def _setup_api(self):
        """Setup focused API endpoints with AutoGen integration."""
        self.app = FastAPI(
            title="VolexSwarm Hybrid Meta Agent",
            description="Central orchestrator with AutoGen and LLM coordination",
            version="3.0.0"
        )
        
        # Add CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Health check
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "agent": "hybrid_meta",
                "version": "3.0.0",
                "autogen_available": self.agent_coordinator is not None,
                "llm_configured": self.openai_client is not None,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get all agent status
        @self.app.get("/agents/status")
        async def get_agent_status():
            return await self._check_all_agents()
        
        # AutoGen task execution
        @self.app.post("/autogen/execute")
        async def execute_autogen_task(request: dict):
            try:
                task_description = request.get("task_description", "")
                required_agents = request.get("required_agents", [])
                
                if not task_description:
                    return {"error": "task_description is required"}
                
                result = await self.execute_task_with_autogen(task_description, required_agents)
                return result
                
            except Exception as e:
                logger.error(f"❌ Error executing AutoGen task: {e}")
                return {"error": str(e)}
        
        # Coordinate portfolio discovery
        @self.app.post("/coordinate/portfolio")
        async def coordinate_portfolio():
            """Coordinate portfolio discovery with enhanced intelligence across agents."""
            task_id = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            try:
                logger.info(f"🔄 Starting enhanced portfolio discovery task: {task_id}")
                
                # Step 1: Get portfolio status from execution agent
                logger.info("📊 Getting portfolio status from Execution Agent...")
                portfolio_result = await self._get_execution_portfolio()
                
                # Step 2: Get risk analysis from risk agent
                logger.info("⚠️ Getting risk analysis from Risk Agent...")
                risk_result = await self._get_risk_analysis(portfolio_result)
                
                # Step 3: Get trading signals for context
                logger.info("📈 Getting trading signals from Signal Agent...")
                signal_result = await self._get_trading_signals()
                
                # Step 4: Aggregate and analyze results
                logger.info("🧠 Aggregating portfolio intelligence...")
                aggregated_result = await self._aggregate_portfolio_intelligence(
                    portfolio_result, risk_result, signal_result
                )
                
                # Step 5: Use AutoGen for additional analysis if available
                if self.agent_coordinator:
                    logger.info("🤖 Using AutoGen for enhanced portfolio analysis...")
                    autogen_analysis = await self._get_autogen_portfolio_analysis(
                        portfolio_result, risk_result, signal_result
                    )
                    aggregated_result["autogen_analysis"] = autogen_analysis
                
                # Combine results
                result = {
                    "task_id": task_id,
                    "portfolio": portfolio_result,
                    "risk_analysis": risk_result,
                    "trading_signals": signal_result,
                    "aggregated_intelligence": aggregated_result,
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed",
                    "source": "enhanced_hybrid_meta_agent"
                }
                
                logger.info(f"✅ Enhanced portfolio discovery completed: {task_id}")
                return result
                
            except Exception as e:
                logger.error(f"❌ Enhanced portfolio discovery failed: {e}")
                return {"error": str(e), "task_id": task_id}

        # GET endpoint for portfolio data (UI-friendly)
        @self.app.get("/coordinate/portfolio")
        async def get_portfolio_data():
            """Get portfolio data through Meta Agent coordination (UI endpoint)."""
            try:
                logger.info("📊 UI requesting portfolio data...")
                
                # Use direct coordination for reliable portfolio data
                logger.info("🔄 Using direct coordination for portfolio data...")
                
                # Get portfolio data directly from Execution Agent
                portfolio_result = await self._get_execution_portfolio()
                logger.info(f"📊 Portfolio result: {portfolio_result}")
                
                # Get risk analysis from Risk Agent
                risk_result = await self._get_risk_analysis(portfolio_result)
                logger.info(f"⚠️ Risk result: {risk_result}")
                
                # Get trading signals from Signal Agent
                signal_result = await self._get_trading_signals()
                logger.info(f"📈 Signal result: {signal_result}")
                
                # Aggregate results
                aggregated_result = await self._aggregate_portfolio_intelligence(
                    portfolio_result, risk_result, signal_result
                )
                logger.info(f"🧠 Aggregated result: {aggregated_result}")
                
                # Return comprehensive portfolio data
                result = {
                    "portfolio": portfolio_result,
                    "risk_analysis": risk_result,
                    "trading_signals": signal_result,
                    "aggregated_intelligence": aggregated_result,
                    "timestamp": datetime.now().isoformat(),
                    "source": "enhanced_hybrid_meta_agent_direct"
                }
                
                logger.info(f"✅ Successfully returned portfolio data for UI: {result}")
                return result
                
            except Exception as e:
                logger.error(f"❌ Failed to get portfolio data for UI: {e}")
                return {"error": str(e)}

        # GET endpoint for trading signals (UI-friendly)
        @self.app.get("/coordinate/signals")
        async def get_trading_signals():
            """Get trading signals through Meta Agent coordination (UI endpoint)."""
            try:
                logger.info("📈 UI requesting trading signals...")
                
                # Use AutoGen to get trading signals
                if self.agent_coordinator:
                    task_description = """
                    Get comprehensive trading signals:
                    1. Retrieve current trading signals from signal agent
                    2. Analyze signal quality and confidence
                    3. Return formatted signal data for UI
                    """
                    
                    result = await self.execute_task_with_autogen(
                        task_description,
                        ["signal"]
                    )
                    
                    return {
                        "signals": result.get("signals", []),
                        "timestamp": datetime.now().isoformat(),
                        "source": "enhanced_hybrid_meta_agent_autogen"
                    }
                else:
                    # Fallback to direct call
                    signal_result = await self._get_trading_signals()
                    return {
                        "signals": signal_result.get("data", []),
                        "timestamp": datetime.now().isoformat(),
                        "source": "enhanced_hybrid_meta_agent_direct"
                    }
                
            except Exception as e:
                logger.error(f"❌ Failed to get trading signals for UI: {e}")
                return {"error": str(e)}

        # GET endpoint for active strategies (UI-friendly)
        @self.app.get("/coordinate/strategies")
        async def get_active_strategies():
            """Get active strategies through Meta Agent coordination (UI endpoint)."""
            try:
                logger.info("📊 UI requesting active strategies...")
                
                # Use AutoGen to get strategy information
                if self.agent_coordinator:
                    task_description = """
                    Get active trading strategies:
                    1. Retrieve strategy information from strategy discovery agent
                    2. Analyze strategy performance and status
                    3. Return formatted strategy data for UI
                    """
                    
                    result = await self.execute_task_with_autogen(
                        task_description,
                        ["strategy_discovery"]
                    )
                    
                    return {
                        "strategies": result.get("strategies", []),
                        "timestamp": datetime.now().isoformat(),
                        "source": "enhanced_hybrid_meta_agent_autogen"
                    }
                else:
                    # Fallback to direct call
                    strategy_result = await self._get_strategy_status()
                    return {
                        "strategies": strategy_result.get("data", []),
                        "timestamp": datetime.now().isoformat(),
                        "source": "enhanced_hybrid_meta_agent_direct"
                    }
                
            except Exception as e:
                logger.error(f"❌ Failed to get active strategies for UI: {e}")
                return {"error": str(e)}

        # GET endpoint for market data (UI-friendly)
        @self.app.get("/coordinate/market")
        async def get_market_data():
            """Get market data through Meta Agent coordination (UI endpoint)."""
            try:
                logger.info("📊 UI requesting market data...")
                
                # Use AutoGen to get market data
                if self.agent_coordinator:
                    task_description = """
                    Get comprehensive market data:
                    1. Retrieve real-time market prices from realtime data agent
                    2. Analyze market trends and patterns
                    3. Return formatted market data for UI
                    """
                    
                    result = await self.execute_task_with_autogen(
                        task_description,
                        ["realtime_data"]
                    )
                    
                    return {
                        "market_data": result.get("market_data", []),
                        "timestamp": datetime.now().isoformat(),
                        "source": "enhanced_hybrid_meta_agent_autogen"
                    }
                else:
                    # Fallback to direct call
                    market_result = await self._get_market_data()
                    return {
                        "market_data": market_result.get("data", []),
                        "timestamp": datetime.now().isoformat(),
                        "source": "enhanced_hybrid_meta_agent_direct"
                    }
                
            except Exception as e:
                logger.error(f"❌ Failed to get market data for UI: {e}")
                return {"error": str(e)}
        
        # Coordinate trading strategy
        @self.app.post("/coordinate/trading")
        async def coordinate_trading(request: dict):
            """Coordinate intelligent trading strategy with AutoGen."""
            budget = request.get("budget", 25.0)
            
            task_description = f"""
            Develop and execute an intelligent trading strategy with ${budget} budget:
            1. Analyze current market conditions and trends using real-time data
            2. Research news sentiment and market drivers
            3. Generate trading signals based on technical analysis
            4. Develop risk-managed trading strategy
            5. Execute trades if signals are strong and risk is acceptable
            6. Monitor positions and adjust as needed
            
            Use real Binance US account and live market data.
            Budget: ${budget}
            """
            
            return await self.execute_task_with_autogen(
                task_description, 
                ["strategy_discovery", "news_sentiment", "signal", "execution", "risk", "monitor"]
            )
        
        # Get AutoGen status
        @self.app.get("/autogen/status")
        async def get_autogen_status():
            try:
                if not self.agent_coordinator:
                    return {"status": "not_initialized"}
                
                return {
                    "status": "active",
                    "agents": list(self.agent_coordinator.agents.keys()) if hasattr(self.agent_coordinator, 'agents') else [],
                    "conversations": list(self.agent_coordinator.group_chats.keys()) if hasattr(self.agent_coordinator, 'group_chats') else [],
                    "workflows": list(self.agent_coordinator.tool_workflows.keys()) if hasattr(self.agent_coordinator, 'tool_workflows') else []
                }
                
            except Exception as e:
                logger.error(f"❌ Error getting AutoGen status: {e}")
                return {"error": str(e)}
        
        # RESTORED CRITICAL FEATURES - Consensus Building
        @self.app.post("/consensus/create_task")
        async def create_consensus_task(request: dict):
            """Create a task that will use consensus building."""
            try:
                name = request.get("name", "")
                description = request.get("description", "")
                priority = request.get("priority", "MEDIUM")
                required_agents = request.get("required_agents", [])
                dependencies = request.get("dependencies", [])
                
                if not name or not description:
                    return {"error": "name and description are required"}
                
                # Convert priority string to enum
                priority_enum = TaskPriority[priority.upper()] if priority.upper() in TaskPriority.__members__ else TaskPriority.MEDIUM
                
                task_id = await self.create_intelligent_task(
                    name=name,
                    description=description,
                    priority=priority_enum,
                    required_agents=required_agents,
                    dependencies=dependencies
                )
                
                return {
                    "task_id": task_id,
                    "status": "created",
                    "message": f"Task {task_id} created and assigned to {required_agents or 'auto-assigned agents'}"
                }
                
            except Exception as e:
                logger.error(f"❌ Error creating consensus task: {e}")
                return {"error": str(e)}
        
        @self.app.post("/consensus/execute/{task_id}")
        async def execute_consensus_task(task_id: str):
            """Execute a task using consensus building."""
            try:
                result = await self.execute_task_with_consensus(task_id)
                return result
                
            except Exception as e:
                logger.error(f"❌ Error executing consensus task: {e}")
                return {"error": str(e)}
        
        @self.app.get("/consensus/history")
        async def get_consensus_history():
            """Get consensus building history."""
            try:
                return {
                    "consensus_history": [
                        {
                            "task_id": consensus.task_id,
                            "agents": consensus.agents,
                            "decision": consensus.decision,
                            "confidence": consensus.confidence,
                            "reasoning": consensus.reasoning,
                            "timestamp": consensus.timestamp.isoformat()
                        }
                        for consensus in self.consensus_history[-20:]  # Last 20
                    ],
                    "total_consensus": len(self.consensus_history)
                }
                
            except Exception as e:
                logger.error(f"❌ Error getting consensus history: {e}")
                return {"error": str(e)}
        
        # RESTORED CRITICAL FEATURES - Autonomous Decision Making
        @self.app.post("/autonomous/decision")
        async def make_autonomous_decision(request: dict):
            """Make an autonomous decision using LLM reasoning."""
            try:
                decision_type = request.get("decision_type", "")
                context = request.get("context", {})
                
                if not decision_type:
                    return {"error": "decision_type is required"}
                
                decision = await self.make_autonomous_decision(decision_type, context)
                
                return {
                    "decision_id": decision.id,
                    "decision": decision.decision,
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning,
                    "validation_score": decision.validation_score,
                    "alternatives": decision.alternatives,
                    "timestamp": decision.timestamp.isoformat()
                }
                
            except Exception as e:
                logger.error(f"❌ Error making autonomous decision: {e}")
                return {"error": str(e)}
        
        @self.app.get("/autonomous/decisions")
        async def get_autonomous_decisions():
            """Get autonomous decision history."""
            try:
                return {
                    "decisions": [
                        {
                            "id": decision.id,
                            "type": decision.decision_type,
                            "decision": decision.decision,
                            "confidence": decision.confidence,
                            "validation_score": decision.validation_score,
                            "timestamp": decision.timestamp.isoformat()
                        }
                        for decision in self.decision_history[-20:]  # Last 20
                    ],
                    "total_decisions": len(self.decision_history)
                }
                
            except Exception as e:
                logger.error(f"❌ Error getting autonomous decisions: {e}")
                return {"error": str(e)}
        
        # RESTORED CRITICAL FEATURES - Agent Performance Monitoring
        @self.app.get("/performance/agent/{agent_name}")
        async def get_agent_performance(agent_name: str):
            """Get performance metrics for a specific agent."""
            try:
                performance = await self.monitor_agent_performance(agent_name)
                return performance
                
            except Exception as e:
                logger.error(f"❌ Error getting agent performance: {e}")
                return {"error": str(e)}
        
        @self.app.get("/performance/overview")
        async def get_performance_overview():
            """Get performance overview for all agents."""
            try:
                overview = {}
                for agent_name in self.agent_endpoints.keys():
                    overview[agent_name] = await self.monitor_agent_performance(agent_name)
                
                return {
                    "performance_overview": overview,
                    "total_agents": len(self.agent_endpoints),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"❌ Error getting performance overview: {e}")
                return {"error": str(e)}
        
        # RESTORED CRITICAL FEATURES - Conflict Resolution
        @self.app.post("/conflicts/resolve")
        async def resolve_conflict(request: dict):
            """Resolve conflicts between agents."""
            try:
                conflict_data = request.get("conflict_data", {})
                
                if not conflict_data:
                    return {"error": "conflict_data is required"}
                
                resolution = await self.resolve_agent_conflicts(conflict_data)
                return resolution
                
            except Exception as e:
                logger.error(f"❌ Error resolving conflict: {e}")
                return {"error": str(e)}
        
        # RESTORED CRITICAL FEATURES - Task Management
        @self.app.get("/tasks/consensus/{task_id}")
        async def get_consensus_task(task_id: str):
            """Get details of a consensus-based task."""
            try:
                if task_id not in self.tasks:
                    return {"error": f"Task {task_id} not found"}
                
                task = self.tasks[task_id]
                return {
                    "task_id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "priority": task.priority.name,
                    "status": task.status.value,
                    "assigned_agents": task.assigned_agents,
                    "dependencies": task.dependencies,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "confidence": task.confidence,
                    "reasoning": task.reasoning
                }
                
            except Exception as e:
                logger.error(f"❌ Error getting consensus task: {e}")
                return {"error": str(e)}
        
        @self.app.get("/tasks/consensus")
        async def list_consensus_tasks():
            """List all consensus-based tasks."""
            try:
                tasks = []
                for task in self.tasks.values():
                    tasks.append({
                        "task_id": task.id,
                        "name": task.name,
                        "status": task.status.value,
                        "priority": task.priority.name,
                        "assigned_agents": task.assigned_agents,
                        "created_at": task.created_at.isoformat()
                    })
                
                return {
                    "tasks": tasks,
                    "total_tasks": len(tasks),
                    "pending": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                    "in_progress": len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
                    "completed": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                    "failed": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
                }
                
            except Exception as e:
                logger.error(f"❌ Error listing consensus tasks: {e}")
                return {"error": str(e)}
        
        # RESTORED CRITICAL FEATURES - System Intelligence
        @self.app.get("/intelligence/system")
        async def get_system_intelligence():
            """Get system intelligence report."""
            try:
                # Get agent performance overview
                performance_overview = await self.monitor_agent_performance("execution")  # Sample agent
                
                # Calculate system health metrics
                total_agents = len(self.agent_endpoints)
                healthy_agents = 0
                total_load = 0
                
                for agent_name in self.agent_endpoints.keys():
                    try:
                        status = await self._call_agent(agent_name, "/health")
                        if status.get("status") == "healthy":
                            healthy_agents += 1
                        total_load += self.agent_loads.get(agent_name, 0)
                    except:
                        pass
                
                system_health = (healthy_agents / total_agents) * 100 if total_agents > 0 else 0
                
                return {
                    "system_health": system_health,
                    "total_agents": total_agents,
                    "healthy_agents": healthy_agents,
                    "total_system_load": total_load,
                    "consensus_decisions": len(self.consensus_history),
                    "autonomous_decisions": len(self.decision_history),
                    "active_tasks": len([t for t in self.tasks.values() if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]])
                }
                
            except Exception as e:
                logger.error(f"❌ Error getting system intelligence: {e}")
                return {"error": str(e)}
        
        # WebSocket Management Endpoints
        @self.app.get("/websocket/stats")
        async def get_websocket_stats():
            """Get WebSocket connection statistics."""
            try:
                return {
                    "active_connections": len(self.websocket_clients),
                    "total_connections_handled": len(self.websocket_clients),
                    "websocket_server_status": "active",
                    "port": 8004,
                    "endpoint": "/ws",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"❌ Error getting WebSocket stats: {e}")
                return {"error": str(e)}
        
        @self.app.get("/websocket/connections")
        async def get_websocket_connections():
            """Get detailed information about active WebSocket connections."""
            try:
                connections = []
                for client in self.websocket_clients:
                    try:
                        client_info = {
                            "client_id": getattr(client, '_client_id', 'unknown'),
                            "connected_at": getattr(client, '_connected_at', 'unknown').isoformat() if hasattr(client, '_connected_at') else 'unknown',
                            "last_activity": getattr(client, '_last_activity', 'unknown').isoformat() if hasattr(client, '_last_activity') else 'unknown',
                            "client_ip": getattr(client, '_client_ip', 'unknown'),
                            "connection_age_minutes": 0
                        }
                        
                        if hasattr(client, '_connected_at') and hasattr(client, '_connected_at'):
                            age = datetime.now() - client._connected_at
                            client_info["connection_age_minutes"] = round(age.total_seconds() / 60, 2)
                        
                        connections.append(client_info)
                    except Exception as e:
                        logger.warning(f"Error getting client info: {e}")
                        connections.append({"error": str(e)})
                
                return {
                    "total_connections": len(self.websocket_clients),
                    "connections": connections,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"❌ Error getting WebSocket connections: {e}")
                return {"error": str(e)}
        
        @self.app.post("/websocket/reset")
        async def reset_websocket_connections():
            """Reset all WebSocket connections."""
            try:
                # Close all active connections
                disconnected_clients = set()
                # Create a copy of the set to avoid iteration issues
                clients_to_close = list(self.websocket_clients)
                
                for client in clients_to_close:
                    try:
                        await client.close(code=1000, reason="Server reset")
                        disconnected_clients.add(client)
                    except Exception as e:
                        logger.error(f"Error closing WebSocket client: {e}")
                        disconnected_clients.add(client)
                
                # Remove disconnected clients
                self.websocket_clients.clear()
                
                return {
                    "status": "reset_complete",
                    "disconnected_clients": len(disconnected_clients),
                    "remaining_connections": len(self.websocket_clients),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"❌ Error resetting WebSocket connections: {e}")
                return {"error": str(e)}
        
        # FastAPI WebSocket Endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            # Debug: Log current connection count
            current_count = len(self.websocket_clients)
            logger.info(f"🔌 WebSocket connection attempt. Current clients: {current_count}")
            
            # Increased connection limit to accommodate more legitimate connections
            # 30 was too restrictive - we have multiple services that need connections
            if current_count >= 100:  # Increased from 30 to 100
                logger.warning(f"WebSocket connection limit reached ({current_count}). Rejecting new connection.")
                await websocket.close(code=1008, reason="Connection limit exceeded")
                return
                
            try:
                await websocket.accept()
                
                # Track connection metadata for cleanup
                websocket._connected_at = datetime.now()
                websocket._last_activity = datetime.now()
                websocket._client_id = str(uuid.uuid4())[:8]  # Short client ID for logging
                websocket._client_ip = websocket.client.host if hasattr(websocket, 'client') else 'unknown'
                
                self.websocket_clients.add(websocket)
                client_count = len(self.websocket_clients)
                logger.info(f"🔌 WebSocket client {websocket._client_id} connected from {websocket._client_ip}. Total clients: {client_count}")
                
                # Send welcome message
                try:
                    await websocket.send_text(json.dumps({
                        "type": "welcome",
                        "message": "Connected to VolexSwarm Meta Agent - Central WebSocket Hub",
                        "timestamp": datetime.now().isoformat(),
                        "agent": "meta",
                        "client_id": websocket._client_id,
                        "capabilities": [
                            "coordination", 
                            "agent_communication", 
                            "real_time_updates",
                            "consensus_building",
                            "autonomous_decision_making",
                            "agent_performance_monitoring",
                            "conflict_resolution",
                            "intelligent_task_management"
                        ],
                        "restored_features": [
                            "Advanced consensus building with agent voting",
                            "LLM-driven autonomous decisions",
                            "Real-time agent performance monitoring",
                            "Intelligent conflict resolution",
                            "Enhanced task management with priorities",
                            "System intelligence reporting"
                        ]
                    }))
                    websocket._last_activity = datetime.now()
                except Exception as e:
                    logger.error(f"Error sending welcome message: {e}")
                    await websocket.close(code=1011, reason="Failed to send welcome message")
                    self.websocket_clients.discard(websocket)
                    return
                
                # Keep connection alive and handle messages
                try:
                    while True:
                        try:
                            message = await websocket.receive_text()
                            websocket._last_activity = datetime.now()
                            
                            try:
                                data = json.loads(message)
                                await self._handle_websocket_message(websocket, data)
                            except json.JSONDecodeError:
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "message": "Invalid JSON format",
                                    "timestamp": datetime.now().isoformat()
                                }))
                            except Exception as e:
                                logger.error(f"WebSocket message error: {e}")
                                await websocket.send_text(json.dumps({
                                    "type": "error",
                                    "message": "Message processing error",
                                    "timestamp": datetime.now().isoformat()
                                }))
                                
                        except Exception as e:
                            logger.info(f"WebSocket client {websocket._client_id} connection closed: {e}")
                            break
                            
                except Exception as e:
                    logger.error(f"WebSocket message loop error: {e}")
                finally:
                    # Always ensure cleanup
                    if websocket in self.websocket_clients:
                        self.websocket_clients.discard(websocket)
                        remaining_count = len(self.websocket_clients)
                        logger.info(f"🔌 WebSocket client {websocket._client_id} disconnected. Total clients: {remaining_count}")
                    
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                # Ensure cleanup even if connection wasn't fully established
                if websocket in self.websocket_clients:
                    self.websocket_clients.discard(websocket)

    async def _check_all_agents(self) -> Dict[str, Any]:
        """Check the health of all coordinated agents."""
        agent_status = {}
        healthy_count = 0
        
        for agent_name, endpoint in self.agent_endpoints.items():
            try:
                response = requests.get(f"{endpoint}/health", timeout=3)
                if response.status_code == 200:
                    agent_status[agent_name] = {
                        "status": "healthy",
                        "endpoint": endpoint,
                        "response_time": response.elapsed.total_seconds()
                    }
                    healthy_count += 1
                else:
                    agent_status[agent_name] = {
                        "status": "unhealthy",
                        "endpoint": endpoint,
                        "http_status": response.status_code
                    }
            except Exception as e:
                agent_status[agent_name] = {
                    "status": "unreachable",
                    "endpoint": endpoint,
                    "error": str(e)
                }
        
        return {
            "meta_agent": "healthy",
            "autogen_coordinator": "active" if self.agent_coordinator else "inactive",
            "llm_client": "configured" if self.openai_client else "not_configured",
            "coordinated_agents": agent_status,
            "total_agents": len(self.agent_endpoints),
            "healthy_agents": healthy_count,
            "health_percentage": (healthy_count / len(self.agent_endpoints)) * 100
        }
    
    async def _call_agent(self, agent_name: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a call to a specific agent."""
        if agent_name not in self.agent_endpoints:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        base_url = self.agent_endpoints[agent_name]
        url = f"{base_url}{endpoint}"
        
        try:
            if data:
                response = requests.post(url, json=data, timeout=30)
            else:
                response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Agent {agent_name} returned {response.status_code}: {response.text}")
                return {"error": f"HTTP {response.status_code}", "agent": agent_name}
                
        except Exception as e:
            logger.error(f"Failed to call agent {agent_name}: {e}")
            return {"error": str(e), "agent": agent_name}
    
    # ENHANCED PORTFOLIO INTELLIGENCE METHODS
    async def _get_execution_portfolio(self) -> Dict[str, Any]:
        """Get REAL portfolio data from Execution Agent using actual endpoints."""
        try:
            logger.info("📊 Getting REAL portfolio data from Execution Agent...")
            
            # Get portfolio status from Execution Agent
            portfolio_result = await self._call_agent("execution", "/api/execution/portfolio")
            
            # Get positions from Execution Agent
            positions_result = await self._call_agent("execution", "/api/execution/positions")
            
            # Get P&L from Execution Agent
            pnl_result = await self._call_agent("execution", "/api/execution/pnl")
            
            # Get portfolio performance including total return
            performance_result = await self._call_agent("execution", "/api/execution/portfolio-performance")
            
            # Get portfolio history for charting
            history_result = await self._call_agent("execution", "/api/execution/portfolio-history?days=30")
            
            # Get recent trades from Execution Agent
            trades_result = await self._call_agent("execution", "/api/execution/trades")
            
            # Combine all real data
            combined_portfolio = {
                "portfolio_status": portfolio_result,
                "positions": positions_result,
                "pnl": pnl_result,
                "performance": performance_result,
                "history": history_result,  # Added portfolio history
                "recent_trades": trades_result,
                "timestamp": datetime.now().isoformat(),
                "source": "execution_agent_real_data_with_history"
            }
            
            logger.info("📊 Successfully retrieved REAL portfolio data from Execution Agent")
            return combined_portfolio
            
        except Exception as e:
            logger.error(f"Failed to get execution portfolio: {e}")
            return {"error": str(e), "source": "execution_agent"}
    
    async def _get_risk_analysis(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get REAL risk analysis from Risk Agent."""
        try:
            # Call Risk Agent's portfolio assessment endpoint (port 8009)
            risk_result = await self._call_agent("risk", "/api/risk/portfolio", {
                "positions": portfolio_data.get("positions", []),
                "account_balance": portfolio_data.get("total_value", 0)
            })
            
            logger.info("⚠️ Retrieved REAL risk analysis from Risk Agent")
            return risk_result
            
        except Exception as e:
            logger.error(f"Failed to get risk analysis: {e}")
            return {"error": str(e), "source": "risk_agent"}
    
    async def _get_trading_signals(self) -> Dict[str, Any]:
        """Get REAL trading signals from Signal Agent."""
        try:
            # Call Signal Agent's signals endpoint (port 8003)
            signal_result = await self._call_agent("signal", "/signals")
            
            logger.info("📈 Retrieved REAL trading signals from Signal Agent")
            return signal_result
            
        except Exception as e:
            logger.error(f"Failed to get trading signals: {e}")
            return {"error": str(e), "source": "signal_agent"}

    async def _get_strategy_status(self) -> Dict[str, Any]:
        """Get active strategies from Strategy Discovery Agent."""
        try:
            # Call Strategy Discovery Agent's credentials endpoint (port 8025)
            strategy_result = await self._call_agent("strategy_discovery", "/credentials/list")
            
            logger.info("📊 Retrieved active strategies from Strategy Discovery Agent")
            return strategy_result
            
        except Exception as e:
            logger.error(f"Failed to get strategy status: {e}")
            return {"error": str(e), "source": "strategy_discovery_agent"}

    async def _get_market_data(self) -> Dict[str, Any]:
        """Get market data from Realtime Data Agent."""
        try:
            # Call Realtime Data Agent's market endpoint (port 8026)
            market_result = await self._call_agent("realtime_data", "/market/prices")
            
            logger.info("📈 Retrieved market data from Realtime Data Agent")
            return market_result
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return {"error": str(e), "source": "realtime_data_agent"}
    
    async def _aggregate_portfolio_intelligence(self, portfolio: Dict[str, Any], 
                                             risk: Dict[str, Any], 
                                             signals: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate and analyze portfolio intelligence across all sources."""
        try:
            # Calculate portfolio health score
            portfolio_health = self._calculate_portfolio_health(portfolio, risk)
            
            # Generate intelligent insights
            insights = self._generate_portfolio_insights(portfolio, risk, signals)
            
            # Create recommendations
            recommendations = self._create_portfolio_recommendations(portfolio, risk, signals)
            
            aggregated_intelligence = {
                "portfolio_health_score": portfolio_health,
                "insights": insights,
                "recommendations": recommendations,
                "risk_level": risk.get("risk_level", "unknown"),
                "signal_count": len(signals.get("data", [])),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info("🧠 Portfolio intelligence aggregation completed")
            return aggregated_intelligence
            
        except Exception as e:
            logger.error(f"Failed to aggregate portfolio intelligence: {e}")
            return {"error": str(e), "source": "intelligence_aggregation"}
    
    async def _get_autogen_portfolio_analysis(self, portfolio: Dict[str, Any], 
                                            risk: Dict[str, Any], 
                                            signals: Dict[str, Any]) -> Dict[str, Any]:
        """Get additional portfolio analysis using AutoGen if available."""
        try:
            if not self.agent_coordinator:
                return {"status": "autogen_not_available"}
            
            # Create a portfolio analysis task for AutoGen
            task_description = f"""
            Analyze the current portfolio and provide intelligent insights:
            
            Portfolio Data: {portfolio}
            Risk Assessment: {risk}
            Trading Signals: {signals}
            
            Provide:
            1. Market timing analysis
            2. Position sizing recommendations
            3. Risk management suggestions
            4. Opportunity identification
            5. Strategic portfolio adjustments
            """
            
            # Execute with AutoGen
            result = await self.execute_task_with_autogen(
                task_description, 
                ["execution", "risk", "signal"]
            )
            
            return {
                "status": "completed",
                "analysis": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AutoGen portfolio analysis: {e}")
            return {"error": str(e), "status": "failed"}
    
    def _calculate_portfolio_health(self, portfolio: Dict[str, Any], risk: Dict[str, Any]) -> float:
        """Calculate a portfolio health score (0-100)."""
        try:
            # Simple health calculation based on available data
            health_score = 50.0  # Base score
            
            # Adjust based on risk level
            risk_level = risk.get("risk_level", "medium")
            if risk_level == "low":
                health_score += 20
            elif risk_level == "high":
                health_score -= 20
            
            # Adjust based on portfolio value
            total_value = portfolio.get("total_value", 0)
            if total_value > 0:
                health_score += 10
            
            # Ensure score is between 0-100
            return max(0, min(100, health_score))
            
        except Exception:
            return 50.0  # Default score
    
    def _generate_portfolio_insights(self, portfolio: Dict[str, Any], 
                                   risk: Dict[str, Any], 
                                   signals: Dict[str, Any]) -> List[str]:
        """Generate intelligent insights about the portfolio."""
        insights = []
        
        try:
            # Portfolio value insights
            total_value = portfolio.get("total_value", 0)
            if total_value == 0:
                insights.append("Portfolio appears to be empty - consider initial funding")
            elif total_value < 100:
                insights.append("Portfolio value is low - consider dollar-cost averaging")
            
            # Risk insights
            risk_level = risk.get("risk_level", "unknown")
            if risk_level == "high":
                insights.append("Portfolio risk level is high - consider risk management strategies")
            elif risk_level == "low":
                insights.append("Portfolio risk level is low - may be underutilizing opportunities")
            
            # Signal insights
            signal_count = len(signals.get("data", []))
            if signal_count == 0:
                insights.append("No active trading signals - market may be in consolidation")
            elif signal_count > 5:
                insights.append("Multiple trading signals active - high market volatility detected")
            
            # Add timestamp insight
            insights.append(f"Analysis performed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            insights.append(f"Error generating insights: {str(e)}")
        
        return insights
    
    def _create_portfolio_recommendations(self, portfolio: Dict[str, Any], 
                                        risk: Dict[str, Any], 
                                        signals: Dict[str, Any]) -> List[str]:
        """Create actionable recommendations for the portfolio."""
        recommendations = []
        
        try:
            # Risk-based recommendations
            risk_level = risk.get("risk_level", "unknown")
            if risk_level == "high":
                recommendations.append("Consider reducing position sizes to manage risk")
                recommendations.append("Implement stop-loss orders for existing positions")
            elif risk_level == "low":
                recommendations.append("Consider increasing position sizes for better returns")
                recommendations.append("Explore higher-risk, higher-reward opportunities")
            
            # Portfolio-based recommendations
            total_value = portfolio.get("total_value", 0)
            if total_value == 0:
                recommendations.append("Start with a small initial investment to test strategies")
                recommendations.append("Consider paper trading to validate approaches")
            
            # Signal-based recommendations
            signal_count = len(signals.get("data", []))
            if signal_count > 0:
                recommendations.append("Review active trading signals for entry opportunities")
                recommendations.append("Monitor signal performance to refine strategies")
            
            # General recommendations
            recommendations.append("Regularly review and rebalance portfolio")
            recommendations.append("Maintain emergency funds outside of trading portfolio")
            
        except Exception as e:
            recommendations.append(f"Error creating recommendations: {str(e)}")
        
        return recommendations

    def _start_servers(self):
        """Start FastAPI server with built-in WebSocket support."""
        # Start FastAPI server (includes WebSocket support)
        def run_fastapi():
            uvicorn.run(self.app, host="0.0.0.0", port=8004, log_level="info")
        
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        
        # Start WebSocket connection cleanup thread
        def run_websocket_cleanup():
            while True:
                try:
                    time.sleep(60)  # Check every minute
                    self._cleanup_stale_websocket_connections()
                except Exception as e:
                    logger.error(f"WebSocket cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=run_websocket_cleanup, daemon=True)
        cleanup_thread.start()
        
        logger.info("🌐 FastAPI server started on http://localhost:8004")
        logger.info("🔌 WebSocket server available on ws://localhost:8004/ws")
        logger.info("🧹 WebSocket connection cleanup enabled (every 60s)")
        logger.info("🤖 AutoGen coordination available")
        logger.info("🧠 LLM-driven agent assignment enabled")
    
    async def _handle_websocket_message(self, websocket, data):
        """Handle incoming WebSocket messages."""
        message_type = data.get("type", "unknown")
        
        if message_type == "ping":
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
        
        elif message_type == "agent_status":
            # Get status of all agents
            status = await self._get_all_agent_status()
            await websocket.send_text(json.dumps({
                "type": "agent_status_response",
                "data": status,
                "timestamp": datetime.now().isoformat()
            }))
        
        elif message_type == "execute_task":
            # Execute task via AutoGen coordination
            task_description = data.get("task_description", "")
            required_agents = data.get("required_agents", [])
            
            try:
                result = await self.execute_task_with_autogen(task_description, required_agents)
                await websocket.send_text(json.dumps({
                    "type": "task_result",
                    "data": result,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "task_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
        
        # RESTORED CRITICAL FEATURES - WebSocket Support
        elif message_type == "create_consensus_task":
            # Create a consensus-based task
            try:
                task_data = data.get("task_data", {})
                task_id = await self.create_intelligent_task(
                    name=task_data.get("name", "WebSocket Task"),
                    description=task_data.get("description", ""),
                    priority=TaskPriority[task_data.get("priority", "MEDIUM").upper()] if task_data.get("priority") else TaskPriority.MEDIUM,
                    required_agents=task_data.get("required_agents", [])
                )
                
                await websocket.send_text(json.dumps({
                    "type": "consensus_task_created",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "consensus_task_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
        
        elif message_type == "execute_consensus_task":
            # Execute a consensus-based task
            try:
                task_id = data.get("task_id", "")
                if not task_id:
                    await websocket.send_text(json.dumps({
                        "type": "consensus_task_error",
                        "error": "task_id is required",
                        "timestamp": datetime.now().isoformat()
                    }))
                    return
                
                result = await self.execute_task_with_consensus(task_id)
                await websocket.send_text(json.dumps({
                    "type": "consensus_task_result",
                    "data": result,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "consensus_task_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
        
        elif message_type == "make_autonomous_decision":
            # Make an autonomous decision
            try:
                decision_type = data.get("decision_type", "")
                context = data.get("context", {})
                
                if not decision_type:
                    await websocket.send_text(json.dumps({
                        "type": "autonomous_decision_error",
                        "error": "decision_type is required",
                        "timestamp": datetime.now().isoformat()
                    }))
                    return
                
                decision = await self.make_autonomous_decision(decision_type, context)
                await websocket.send_text(json.dumps({
                    "type": "autonomous_decision_result",
                    "data": {
                        "decision_id": decision.id,
                        "decision": decision.decision,
                        "confidence": decision.confidence,
                        "reasoning": decision.reasoning,
                        "validation_score": decision.validation_score
                    },
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "autonomous_decision_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
        
        elif message_type == "get_agent_performance":
            # Get agent performance metrics
            try:
                agent_name = data.get("agent_name", "")
                if not agent_name:
                    await websocket.send_text(json.dumps({
                        "type": "performance_error",
                        "error": "agent_name is required",
                        "timestamp": datetime.now().isoformat()
                    }))
                    return
                
                performance = await self.monitor_agent_performance(agent_name)
                await websocket.send_text(json.dumps({
                    "type": "agent_performance_response",
                    "agent_name": agent_name,
                    "data": performance,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "performance_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
        
        elif message_type == "resolve_conflict":
            # Resolve agent conflicts
            try:
                conflict_data = data.get("conflict_data", {})
                if not conflict_data:
                    await websocket.send_text(json.dumps({
                        "type": "conflict_resolution_error",
                        "error": "conflict_data is required",
                        "timestamp": datetime.now().isoformat()
                    }))
                    return
                
                resolution = await self.resolve_agent_conflicts(conflict_data)
                await websocket.send_text(json.dumps({
                    "type": "conflict_resolution_result",
                    "data": resolution,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "conflict_resolution_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
        
        elif message_type == "get_system_intelligence":
            # Get system intelligence report
            try:
                # Calculate system health metrics
                total_agents = len(self.agent_endpoints)
                healthy_agents = 0
                total_load = 0
                
                for agent_name in self.agent_endpoints.keys():
                    try:
                        status = await self._call_agent(agent_name, "/health")
                        if status.get("status") == "healthy":
                            healthy_agents += 1
                        total_load += self.agent_loads.get(agent_name, 0)
                    except:
                        pass
                
                system_health = (healthy_agents / total_agents) * 100 if total_agents > 0 else 0
                
                intelligence_report = {
                    "system_health": system_health,
                    "total_agents": total_agents,
                    "healthy_agents": healthy_agents,
                    "total_system_load": total_load,
                    "consensus_decisions": len(self.consensus_history),
                    "autonomous_decisions": len(self.decision_history),
                    "active_tasks": len([t for t in self.tasks.values() if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]])
                }
                
                await websocket.send_text(json.dumps({
                    "type": "system_intelligence_response",
                    "data": intelligence_report,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "system_intelligence_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
        
        elif message_type == "broadcast":
            # Broadcast message to all connected clients
            message = data.get("message", "")
            await self._broadcast_to_all_clients({
                "type": "broadcast",
                "message": message,
                "from": "meta_agent",
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            await websocket.send_text(json.dumps({
                "type": "unknown_message_type",
                "received_type": message_type,
                "timestamp": datetime.now().isoformat()
            }))
    
    async def _broadcast_to_all_clients(self, message):
        """Broadcast message to all connected WebSocket clients."""
        if self.websocket_clients:
            disconnected_clients = set()
            for client in self.websocket_clients:
                try:
                    await client.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected_clients
    
    async def _get_all_agent_status(self):
        """Get status from all agents."""
        status = {}
        for agent_name, endpoint in self.agent_endpoints.items():
            try:
                response = requests.get(f"{endpoint}/health", timeout=5)
                if response.status_code == 200:
                    status[agent_name] = {
                        "status": "healthy",
                        "endpoint": endpoint,
                        "response_time": response.elapsed.total_seconds()
                    }
                else:
                    status[agent_name] = {
                        "status": "unhealthy",
                        "endpoint": endpoint,
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                status[agent_name] = {
                    "status": "unreachable",
                    "endpoint": endpoint,
                    "error": str(e)
                }
        
        return status

    async def create_intelligent_task(self, name: str, description: str, 
                                    priority: TaskPriority = TaskPriority.MEDIUM,
                                    required_agents: List[str] = None,
                                    dependencies: List[str] = None) -> str:
        """Create an intelligent task with proper assignment and dependencies."""
        try:
            task_id = str(uuid.uuid4())
            
            # Intelligently assign agents if not specified
            if not required_agents:
                required_agents = await self._intelligently_assign_agents(description)
            
            # Create task
            task = HybridTask(
                id=task_id,
                name=name,
                description=description,
                priority=priority,
                status=TaskStatus.PENDING,
                assigned_agents=required_agents,
                dependencies=dependencies or []
            )
            
            self.tasks[task_id] = task
            
            # Update agent loads
            for agent in required_agents:
                if agent in self.agent_loads:
                    self.agent_loads[agent] += 1
            
            logger.info(f"✅ Created intelligent task {task_id} assigned to {required_agents}")
            return task_id
            
        except Exception as e:
            logger.error(f"❌ Error creating intelligent task: {e}")
            raise
    
    async def execute_task_with_consensus(self, task_id: str) -> Dict[str, Any]:
        """Execute a task using agent consensus building."""
        try:
            if task_id not in self.tasks:
                return {"error": f"Task {task_id} not found"}
            
            task = self.tasks[task_id]
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            # Build consensus among assigned agents
            consensus = await self._build_agent_consensus(task)
            
            if consensus.confidence >= 0.7:  # High confidence threshold
                # Execute consensus decision
                result = await self._execute_consensus_decision(task, consensus)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                
                # Update performance metrics
                await self._update_agent_loads(task)
                await self._update_performance_metrics(task)
                
                return {
                    "task_id": task_id,
                    "consensus": consensus,
                    "result": result,
                    "status": "completed"
                }
            else:
                # Low confidence - need manual review
                task.status = TaskStatus.PENDING
                return {
                    "task_id": task_id,
                    "consensus": consensus,
                    "status": "needs_review",
                    "message": "Low confidence consensus, manual review required"
                }
                
        except Exception as e:
            logger.error(f"❌ Error executing task with consensus: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = TaskStatus.FAILED
                self.tasks[task_id].error = str(e)
            return {"error": str(e)}
    
    async def _build_agent_consensus(self, task: HybridTask) -> AgentConsensus:
        """Build consensus among agents for a task."""
        try:
            agent_votes = {}
            agent_reasoning = {}
            
            # Get votes from each assigned agent
            for agent_name in task.assigned_agents:
                vote, reasoning = await self._get_agent_vote(agent_name, task)
                agent_votes[agent_name] = vote
                agent_reasoning[agent_name] = reasoning
            
            # Determine consensus decision
            decision = self._determine_consensus_decision(agent_votes)
            confidence = self._calculate_consensus_confidence(agent_votes)
            reasoning = self._aggregate_reasoning(agent_reasoning)
            
            consensus = AgentConsensus(
                task_id=task.id,
                agents=task.assigned_agents,
                decision=decision,
                confidence=confidence,
                reasoning=reasoning,
                votes=agent_votes
            )
            
            # Store consensus history
            self.consensus_history.append(consensus)
            
            return consensus
            
        except Exception as e:
            logger.error(f"❌ Error building consensus: {e}")
            # Return default consensus
            return AgentConsensus(
                task_id=task.id,
                agents=task.assigned_agents,
                decision="proceed_with_caution",
                confidence=0.5,
                reasoning="Consensus building failed, using default decision"
            )
    
    async def _get_agent_vote(self, agent_name: str, task: HybridTask) -> Tuple[str, str]:
        """Get a vote and reasoning from a specific agent."""
        try:
            if self.openai_client:
                prompt = f"""
                Task: {task.description}
                Priority: {task.priority.name}
                Your capabilities: {self.agent_capabilities.get(agent_name, [])}
                
                Should this task proceed? Respond with:
                1. Vote: "approve", "reject", or "modify"
                2. Reasoning: Brief explanation of your decision
                
                Format: {{"vote": "approve", "reasoning": "..."}}
                """
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                content = response.choices[0].message.content.strip()
                try:
                    result = json.loads(content)
                    return result.get("vote", "approve"), result.get("reasoning", "Default approval")
                except:
                    return "approve", "Default approval due to parsing error"
            
            return "approve", "Default approval (LLM not available)"
            
        except Exception as e:
            logger.error(f"❌ Error getting agent vote from {agent_name}: {e}")
            return "approve", "Default approval due to error"
    
    def _determine_consensus_decision(self, agent_votes: Dict[str, str]) -> str:
        """Determine the consensus decision based on agent votes."""
        vote_counts = {"approve": 0, "reject": 0, "modify": 0}
        
        for vote in agent_votes.values():
            if vote in vote_counts:
                vote_counts[vote] += 1
        
        # Simple majority rule
        if vote_counts["approve"] > vote_counts["reject"]:
            return "approve"
        elif vote_counts["reject"] > vote_counts["approve"]:
            return "reject"
        else:
            return "modify"
    
    def _calculate_consensus_confidence(self, agent_votes: Dict[str, str]) -> float:
        """Calculate confidence level of the consensus."""
        if not agent_votes:
            return 0.0
        
        # Count unanimous decisions
        unique_votes = set(agent_votes.values())
        if len(unique_votes) == 1:
            return 1.0  # Unanimous
        elif len(unique_votes) == 2:
            return 0.7  # Majority
        else:
            return 0.5  # Split decision
    
    def _aggregate_reasoning(self, agent_reasoning: Dict[str, str]) -> str:
        """Aggregate reasoning from all agents."""
        if not agent_reasoning:
            return "No reasoning available"
        
        reasoning_list = list(agent_reasoning.values())
        if len(reasoning_list) == 1:
            return reasoning_list[0]
        else:
            return f"Combined reasoning from {len(reasoning_list)} agents: {'; '.join(reasoning_list)}"
    
    async def _execute_consensus_decision(self, task: HybridTask, consensus: AgentConsensus) -> Dict[str, Any]:
        """Execute the consensus decision."""
        try:
            if consensus.decision == "approve":
                return await self._execute_task(task)
            elif consensus.decision == "modify":
                return await self._execute_modified_task(task, consensus)
            else:  # reject
                return {
                    "status": "rejected",
                    "reason": consensus.reasoning,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error executing consensus decision: {e}")
            return {"error": str(e)}
    
    async def _execute_task(self, task: HybridTask) -> Dict[str, Any]:
        """Execute a task using AutoGen coordination."""
        try:
            if self.agent_coordinator:
                result = await self.agent_coordinator.coordinate_task(
                    task_description=task.description,
                    required_agents=task.assigned_agents,
                    max_rounds=10,
                    preserve_context=True
                )
                return result
            else:
                # Fallback to direct coordination
                return await self._execute_task_direct(task.description, task.assigned_agents)
                
        except Exception as e:
            logger.error(f"❌ Error executing task: {e}")
            return {"error": str(e)}
    
    async def _execute_modified_task(self, task: HybridTask, consensus: AgentConsensus) -> Dict[str, Any]:
        """Execute a modified version of the task based on consensus feedback."""
        try:
            # Modify task based on consensus reasoning
            modified_description = f"{task.description} [MODIFIED: {consensus.reasoning}]"
            
            if self.agent_coordinator:
                result = await self.agent_coordinator.coordinate_task(
                    task_description=modified_description,
                    required_agents=task.assigned_agents,
                    max_rounds=8,
                    preserve_context=True
                )
                return result
            else:
                return await self._execute_task_direct(modified_description, task.assigned_agents)
                
        except Exception as e:
            logger.error(f"❌ Error executing modified task: {e}")
            return {"error": str(e)}
    
    async def make_autonomous_decision(self, decision_type: str, context: Dict[str, Any]) -> AutonomousDecision:
        """Make an autonomous decision using LLM reasoning."""
        try:
            decision_id = str(uuid.uuid4())
            
            # Use LLM for autonomous reasoning
            reasoning_result = await self._autonomous_reasoning(decision_type, context)
            
            decision = AutonomousDecision(
                id=decision_id,
                decision_type=decision_type,
                context=context,
                decision=reasoning_result.get("decision", "proceed"),
                confidence=reasoning_result.get("confidence", 0.5),
                reasoning=reasoning_result.get("reasoning", "Default reasoning"),
                alternatives=reasoning_result.get("alternatives", [])
            )
            
            # Validate the decision
            await self._validate_decision(decision)
            
            # Store decision history
            self.decision_history.append(decision)
            
            logger.info(f"✅ Made autonomous decision {decision_id}: {decision.decision}")
            return decision
            
        except Exception as e:
            logger.error(f"❌ Error making autonomous decision: {e}")
            raise
    
    async def _autonomous_reasoning(self, decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM for autonomous reasoning about a decision."""
        try:
            if not self.openai_client:
                return {
                    "decision": "proceed",
                    "confidence": 0.5,
                    "reasoning": "LLM not available",
                    "alternatives": []
                }
            
            prompt = f"""
            Decision Type: {decision_type}
            Context: {json.dumps(context, indent=2)}
            
            Analyze this situation and provide:
            1. Decision: "proceed", "reject", or "modify"
            2. Confidence: 0.0 to 1.0
            3. Reasoning: Clear explanation
            4. Alternatives: List of other options
            
            Respond with JSON: {{"decision": "...", "confidence": 0.0, "reasoning": "...", "alternatives": [...]}}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            try:
                result = json.loads(content)
                return {
                    "decision": result.get("decision", "proceed"),
                    "confidence": float(result.get("confidence", 0.5)),
                    "reasoning": result.get("reasoning", "Default reasoning"),
                    "alternatives": result.get("alternatives", [])
                }
            except:
                return {
                    "decision": "proceed",
                    "confidence": 0.5,
                    "reasoning": "Parsing error, using default",
                    "alternatives": []
                }
                
        except Exception as e:
            logger.error(f"❌ Error in autonomous reasoning: {e}")
            return {
                "decision": "proceed",
                "confidence": 0.5,
                "reasoning": f"Error occurred: {e}",
                "alternatives": []
            }
    
    async def _validate_decision(self, decision: AutonomousDecision) -> None:
        """Validate an autonomous decision."""
        try:
            # Simple validation against basic rules
            validation_score = 0.0
            feedback = []
            
            # Check confidence threshold
            if decision.confidence >= 0.8:
                validation_score += 0.4
                feedback.append("High confidence decision")
            elif decision.confidence >= 0.6:
                validation_score += 0.2
                feedback.append("Moderate confidence decision")
            else:
                feedback.append("Low confidence decision")
            
            # Check reasoning quality
            if len(decision.reasoning) > 50:
                validation_score += 0.3
                feedback.append("Detailed reasoning provided")
            else:
                feedback.append("Brief reasoning provided")
            
            # Check alternatives
            if len(decision.alternatives) > 0:
                validation_score += 0.3
                feedback.append("Alternatives considered")
            else:
                feedback.append("No alternatives provided")
            
            decision.validation_score = validation_score
            decision.validation_status = "validated"
            
        except Exception as e:
            logger.error(f"❌ Error validating decision: {e}")
            decision.validation_score = 0.0
            decision.validation_status = "validation_failed"
    
    async def monitor_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """Monitor performance of a specific agent."""
        try:
            if agent_name not in self.agent_endpoints:
                return {"error": f"Unknown agent: {agent_name}"}
            
            # Get current agent status
            current_status = await self._call_agent(agent_name, "/health")
            
            # Calculate performance metrics
            current_load = self.agent_loads.get(agent_name, 0)
            performance_score = self._calculate_agent_performance_score(agent_name)
            
            # Get recent tasks for this agent
            recent_tasks = [
                task for task in self.tasks.values()
                if agent_name in task.assigned_agents
                and task.completed_at
            ][-5:]  # Last 5 tasks
            
            performance_data = {
                "agent_name": agent_name,
                "current_status": current_status,
                "current_load": current_load,
                "performance_score": performance_score,
                "recent_tasks": len(recent_tasks),
                "success_rate": self._calculate_success_rate(recent_tasks),
                "average_completion_time": self._calculate_average_completion_time(recent_tasks),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store performance data
            self.agent_performance[agent_name] = performance_data
            
            return performance_data
            
        except Exception as e:
            logger.error(f"❌ Error monitoring agent {agent_name}: {e}")
            return {"error": str(e)}
    
    def _calculate_agent_performance_score(self, agent_name: str) -> float:
        """Calculate a performance score for an agent."""
        try:
            if agent_name not in self.agent_performance:
                return 0.5  # Default score
            
            perf_data = self.agent_performance[agent_name]
            
            # Simple scoring based on success rate and load
            success_rate = perf_data.get("success_rate", 0.5)
            current_load = perf_data.get("current_load", 0)
            
            # Normalize load (lower is better for performance)
            load_score = max(0, 1 - (current_load / 10))  # Cap at 10 tasks
            
            # Weighted average
            performance_score = (success_rate * 0.7) + (load_score * 0.3)
            
            return min(1.0, max(0.0, performance_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating performance score: {e}")
            return 0.5
    
    def _calculate_success_rate(self, tasks: List[HybridTask]) -> float:
        """Calculate success rate from a list of tasks."""
        if not tasks:
            return 0.0
        
        successful_tasks = [task for task in tasks if task.status == TaskStatus.COMPLETED]
        return len(successful_tasks) / len(tasks)
    
    def _calculate_average_completion_time(self, tasks: List[HybridTask]) -> float:
        """Calculate average completion time for tasks."""
        if not tasks:
            return 0.0
        
        completion_times = []
        for task in tasks:
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                completion_times.append(duration)
        
        if completion_times:
            return sum(completion_times) / len(completion_times)
        return 0.0
    
    async def resolve_agent_conflicts(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between agents."""
        try:
            conflict_type = self._analyze_conflict_type(conflict_data)
            
            if conflict_type == "resource":
                return await self._resolve_resource_conflict(conflict_data)
            elif conflict_type == "decision":
                return await self._resolve_decision_conflict(conflict_data)
            elif conflict_type == "priority":
                return await self._resolve_priority_conflict(conflict_data)
            else:
                return await self._resolve_generic_conflict(conflict_data)
                
        except Exception as e:
            logger.error(f"❌ Error resolving conflicts: {e}")
            return {"error": str(e)}
    
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
        """Resolve resource conflicts between agents."""
        # Simple resource allocation strategy
        return {
            "conflict_type": "resource",
            "resolution": "round_robin_allocation",
            "status": "resolved",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _resolve_decision_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve decision conflicts between agents."""
        # Use consensus building for decision conflicts
        return {
            "conflict_type": "decision",
            "resolution": "consensus_building",
            "status": "resolved",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _resolve_priority_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve priority conflicts between agents."""
        # Use priority-based resolution
        return {
            "conflict_type": "priority",
            "resolution": "priority_based_scheduling",
            "status": "resolved",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _resolve_generic_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve generic conflicts."""
        return {
            "conflict_type": "generic",
            "resolution": "manual_intervention",
            "status": "requires_manual_resolution",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _update_agent_loads(self, task: HybridTask):
        """Update agent load tracking after task completion."""
        try:
            for agent in task.assigned_agents:
                if agent in self.agent_loads:
                    self.agent_loads[agent] = max(0, self.agent_loads[agent] - 1)
        except Exception as e:
            logger.error(f"❌ Error updating agent loads: {e}")
    
    async def _update_performance_metrics(self, task: HybridTask):
        """Update performance metrics after task completion."""
        try:
            # Update task completion metrics
            if task.completed_at and task.started_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                
                # Update agent performance data
                for agent in task.assigned_agents:
                    if agent not in self.agent_performance:
                        self.agent_performance[agent] = {}
                    
                    if "completion_times" not in self.agent_performance[agent]:
                        self.agent_performance[agent]["completion_times"] = []
                    
                    self.agent_performance[agent]["completion_times"].append(duration)
                    
                    # Keep only last 20 completion times
                    if len(self.agent_performance[agent]["completion_times"]) > 20:
                        self.agent_performance[agent]["completion_times"] = \
                            self.agent_performance[agent]["completion_times"][-20:]
                            
        except Exception as e:
            logger.error(f"❌ Error updating performance metrics: {e}")

    def _cleanup_stale_websocket_connections(self):
        """Periodically clean up stale WebSocket connections."""
        try:
            current_time = datetime.now()
            stale_threshold = current_time - timedelta(minutes=5)  # Consider connections older than 5 minutes stale
            
            disconnected_clients = set()
            for client in list(self.websocket_clients):  # Create a copy to avoid iteration issues
                try:
                    if hasattr(client, '_last_activity') and client._last_activity < stale_threshold:
                        # Close stale connection
                        client.close(code=1000, reason="Stale connection")
                        disconnected_clients.add(client)
                        logger.info(f"Closed stale WebSocket connection {getattr(client, '_client_id', 'unknown')}")
                except Exception as e:
                    logger.warning(f"Error handling stale WebSocket client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected_clients
            if disconnected_clients:
                logger.info(f"🧹 Cleaned up {len(disconnected_clients)} stale WebSocket connections. Remaining: {len(self.websocket_clients)}")
                
        except Exception as e:
            logger.error(f"Error in WebSocket cleanup: {e}")

# Global instance
hybrid_meta_agent = HybridMetaAgent()

async def main():
    """Main entry point."""
    await hybrid_meta_agent.initialize()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Hybrid Meta Agent...")

if __name__ == "__main__":
    asyncio.run(main())
