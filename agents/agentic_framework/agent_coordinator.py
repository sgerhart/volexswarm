"""
Enhanced Agent Coordinator for VolexSwarm Phase 4

This module provides the advanced coordination layer for AutoGen agents,
managing group chat, agent interactions, MCP tool orchestration, and
multi-agent collaboration with context preservation and conversation management.
"""

import autogen
from typing import Dict, Any, List, Optional, Callable
import asyncio
import logging
import json
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import uuid

from .agent_templates import (
    ResearchAgent, SignalAgent, ExecutionAgent, StrategyAgent,
    RiskAgent, ComplianceAgent, MetaAgent, BacktestAgent, OptimizeAgent
)
from .mcp_tools import MCPToolRegistry, create_mcp_tool_registry

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Context for ongoing conversations"""
    conversation_id: str
    topic: str
    participants: List[str]
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class AgentInteraction:
    """Record of agent interaction"""
    interaction_id: str
    timestamp: datetime
    from_agent: str
    to_agent: str
    message: str
    tool_used: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolWorkflow:
    """Definition of a tool workflow"""
    workflow_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    required_agents: List[str]
    expected_output: str
    created_at: datetime = field(default_factory=datetime.now)

class EnhancedAgentCoordinator:
    """Enhanced coordinator for AutoGen agents with Phase 4 features"""
    
    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.agents: Dict[str, Any] = {}
        self.group_chats: Dict[str, Any] = {}
        self.mcp_registry = create_mcp_tool_registry()
        self.interaction_history: List[AgentInteraction] = []
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        self.performance_metrics: Dict[str, Any] = defaultdict(dict)
        self.tool_workflows: Dict[str, ToolWorkflow] = {}
        self.agent_memory: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Initialize all agents
        self._initialize_agents()
        self._create_predefined_workflows()
        
    def _initialize_agents(self):
        """Initialize all AutoGen agents"""
        logger.info("Initializing AutoGen agents...")
        
        # Create agent instances
        self.agents["research"] = ResearchAgent(self.llm_config)
        self.agents["signal"] = SignalAgent(self.llm_config)
        self.agents["execution"] = ExecutionAgent(self.llm_config)
        self.agents["strategy"] = StrategyAgent(self.llm_config)
        self.agents["risk"] = RiskAgent(self.llm_config)
        self.agents["compliance"] = ComplianceAgent(self.llm_config)
        self.agents["meta"] = MetaAgent(self.llm_config)
        self.agents["backtest"] = BacktestAgent(self.llm_config)
        self.agents["optimize"] = OptimizeAgent(self.llm_config)
        
        # Add MCP tools to agents
        self._assign_tools_to_agents()
        
        logger.info(f"Initialized {len(self.agents)} agents")
        
    def _assign_tools_to_agents(self):
        """Assign MCP tools to appropriate agents"""
        logger.info("Assigning MCP tools to agents...")
        
        # Research Agent Tools
        research_tools = self.mcp_registry.get_tools_by_category("research")
        for tool in research_tools:
            self.agents["research"].add_tool(tool)
            
        # Signal Agent Tools
        analysis_tools = self.mcp_registry.get_tools_by_category("analysis")
        for tool in analysis_tools:
            self.agents["signal"].add_tool(tool)
            
        # Execution Agent Tools
        trading_tools = self.mcp_registry.get_tools_by_category("trading")
        for tool in trading_tools:
            self.agents["execution"].add_tool(tool)
            
        # Risk Agent Tools
        risk_tools = self.mcp_registry.get_tools_by_category("risk_management")
        for tool in risk_tools:
            self.agents["risk"].add_tool(tool)
            self.agents["compliance"].add_tool(tool)
            
        # All agents get access to basic tools
        basic_tools = self.mcp_registry.get_tools_by_permission("research")
        for agent_name, agent in self.agents.items():
            for tool in basic_tools:
                agent.add_tool(tool)
                
        logger.info("MCP tools assigned to agents")

    def _create_predefined_workflows(self):
        """Create predefined tool workflows for common tasks"""
        logger.info("Creating predefined tool workflows...")
        
        # Market Analysis Workflow
        market_analysis_workflow = ToolWorkflow(
            workflow_id="market_analysis",
            name="Market Analysis Workflow",
            description="Complete market analysis including research, sentiment, and technical analysis",
            steps=[
                {"step": 1, "agent": "research", "action": "conduct_market_research", "tool": "scrape_crypto_news"},
                {"step": 2, "agent": "research", "action": "analyze_sentiment", "tool": "analyze_sentiment"},
                {"step": 3, "agent": "signal", "action": "technical_analysis", "tool": "calculate_rsi"},
                {"step": 4, "agent": "signal", "action": "generate_signals", "tool": "predict_signal"}
            ],
            required_agents=["research", "signal"],
            expected_output="Comprehensive market analysis with sentiment and technical signals"
        )
        self.tool_workflows["market_analysis"] = market_analysis_workflow
        
        # Risk Assessment Workflow
        risk_assessment_workflow = ToolWorkflow(
            workflow_id="risk_assessment",
            name="Risk Assessment Workflow",
            description="Complete risk assessment including position sizing and portfolio risk",
            steps=[
                {"step": 1, "agent": "risk", "action": "calculate_position_size", "tool": "calculate_position_size"},
                {"step": 2, "agent": "risk", "action": "assess_portfolio_risk", "tool": "assess_portfolio_risk"},
                {"step": 3, "agent": "risk", "action": "check_risk_limits", "tool": "check_risk_limits"}
            ],
            required_agents=["risk"],
            expected_output="Risk assessment with position sizing and portfolio risk analysis"
        )
        self.tool_workflows["risk_assessment"] = risk_assessment_workflow
        
        # Trading Execution Workflow
        trading_execution_workflow = ToolWorkflow(
            workflow_id="trading_execution",
            name="Trading Execution Workflow",
            description="Complete trading execution including order placement and compliance",
            steps=[
                {"step": 1, "agent": "execution", "action": "place_order", "tool": "place_market_order"},
                {"step": 2, "agent": "compliance", "action": "log_trade", "tool": "audit_trade"},
                {"step": 3, "agent": "compliance", "action": "compliance_check", "tool": "detect_suspicious_activity"}
            ],
            required_agents=["execution", "compliance"],
            expected_output="Trade execution with compliance logging and checks"
        )
        self.tool_workflows["trading_execution"] = trading_execution_workflow
        
        logger.info(f"Created {len(self.tool_workflows)} predefined workflows")

    def create_group_chat(self, agents_to_include: Optional[List[str]] = None, 
                         conversation_id: Optional[str] = None) -> str:
        """Create AutoGen group chat with specified agents and conversation management"""
        if agents_to_include is None:
            agents_to_include = list(self.agents.keys())
            
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            
        # Get AutoGen agent instances
        autogen_agents = []
        for agent_name in agents_to_include:
            if agent_name in self.agents:
                autogen_agents.append(self.agents[agent_name].get_agent())
                
        # Create group chat manager
        group_chat = autogen.GroupChatManager(
            groupchat=autogen.GroupChat(
                agents=autogen_agents,
                messages=[],
                max_round=50
            ),
            llm_config=self.llm_config
        )
        
        self.group_chats[conversation_id] = {
            "group_chat": group_chat,
            "agents": agents_to_include,
            "created_at": datetime.now(),
            "message_count": 0
        }
        
        # Create conversation context
        self.conversation_contexts[conversation_id] = ConversationContext(
            conversation_id=conversation_id,
            topic="General Discussion",
            participants=agents_to_include
        )
        
        logger.info(f"Created group chat {conversation_id} with {len(autogen_agents)} agents")
        return conversation_id

    async def initiate_conversation(self, topic: str, 
                                  participants: List[str],
                                  initial_message: str,
                                  context_data: Optional[Dict[str, Any]] = None) -> str:
        """Initiate a new conversation with context preservation"""
        
        conversation_id = str(uuid.uuid4())
        
        # Create group chat
        self.create_group_chat(participants, conversation_id)
        
        # Set up conversation context
        self.conversation_contexts[conversation_id] = ConversationContext(
            conversation_id=conversation_id,
            topic=topic,
            participants=participants,
            context_data=context_data or {}
        )
        
        # Add initial message to context
        self.conversation_contexts[conversation_id].messages.append({
            "timestamp": datetime.now().isoformat(),
            "from": "coordinator",
            "message": initial_message,
            "type": "initiation"
        })
        
        # Record interaction
        interaction = AgentInteraction(
            interaction_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            from_agent="coordinator",
            to_agent="group",
            message=initial_message,
            conversation_id=conversation_id,
            context_data=context_data or {}
        )
        self.interaction_history.append(interaction)
        
        logger.info(f"Initiated conversation {conversation_id} on topic: {topic}")
        return conversation_id

    async def send_message(self, conversation_id: str, 
                          from_agent: str, 
                          message: str,
                          context_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message in an existing conversation with context preservation"""
        
        if conversation_id not in self.conversation_contexts:
            return {"success": False, "error": "Conversation not found"}
            
        if conversation_id not in self.group_chats:
            return {"success": False, "error": "Group chat not found"}
            
        # Update conversation context
        context = self.conversation_contexts[conversation_id]
        context.messages.append({
            "timestamp": datetime.now().isoformat(),
            "from": from_agent,
            "message": message,
            "type": "message"
        })
        context.last_updated = datetime.now()
        
        if context_data:
            context.context_data.update(context_data)
        
        # Record interaction
        interaction = AgentInteraction(
            interaction_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            from_agent=from_agent,
            to_agent="group",
            message=message,
            conversation_id=conversation_id,
            context_data=context_data or {}
        )
        self.interaction_history.append(interaction)
        
        # Update group chat message count
        self.group_chats[conversation_id]["message_count"] += 1
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message_id": interaction.interaction_id,
            "timestamp": datetime.now().isoformat()
        }

    async def execute_tool_workflow(self, workflow_id: str, 
                                  parameters: Dict[str, Any],
                                  conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a predefined tool workflow with coordination"""
        
        if workflow_id not in self.tool_workflows:
            return {"success": False, "error": f"Workflow {workflow_id} not found"}
            
        workflow = self.tool_workflows[workflow_id]
        
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            self.create_group_chat(workflow.required_agents, conversation_id)
        
        # Set up conversation context for workflow
        self.conversation_contexts[conversation_id] = ConversationContext(
            conversation_id=conversation_id,
            topic=f"Workflow: {workflow.name}",
            participants=workflow.required_agents,
            context_data={"workflow_id": workflow_id, "parameters": parameters}
        )
        
        workflow_results = []
        
        try:
            # Execute each step in the workflow
            for step in workflow.steps:
                agent_name = step["agent"]
                action = step["action"]
                tool_name = step.get("tool")
                
                if agent_name not in self.agents:
                    workflow_results.append({
                        "step": step["step"],
                        "status": "error",
                        "error": f"Agent {agent_name} not found"
                    })
                    continue
                
                # Execute the step
                step_result = await self._execute_workflow_step(
                    agent_name, action, tool_name, parameters, conversation_id
                )
                
                workflow_results.append({
                    "step": step["step"],
                    "agent": agent_name,
                    "action": action,
                    "tool": tool_name,
                    "status": "success" if step_result["success"] else "error",
                    "result": step_result
                })
                
                # Update conversation context with step result
                self.conversation_contexts[conversation_id].context_data[f"step_{step['step']}_result"] = step_result
                
            return {
                "success": True,
                "workflow_id": workflow_id,
                "conversation_id": conversation_id,
                "steps": workflow_results,
                "expected_output": workflow.expected_output,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e),
                "steps": workflow_results,
                "timestamp": datetime.now().isoformat()
            }

    async def _execute_workflow_step(self, agent_name: str, action: str, 
                                   tool_name: Optional[str], parameters: Dict[str, Any],
                                   conversation_id: str) -> Dict[str, Any]:
        """Execute a single workflow step"""
        
        agent = self.agents[agent_name]
        
        try:
            # Execute the action on the agent
            if hasattr(agent, action):
                method = getattr(agent, action)
                if asyncio.iscoroutinefunction(method):
                    result = await method(**parameters)
                else:
                    result = method(**parameters)
            else:
                # Try to find and execute the tool
                if tool_name:
                    tool = self.mcp_registry.get_tool(tool_name)
                    if tool:
                        result = tool.function(**parameters)
                    else:
                        result = {"error": f"Tool {tool_name} not found"}
                else:
                    result = {"error": f"Action {action} not found on agent {agent_name}"}
            
            # Record the interaction
            interaction = AgentInteraction(
                interaction_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                from_agent="coordinator",
                to_agent=agent_name,
                message=f"Executing {action}",
                tool_used=tool_name,
                result=result,
                conversation_id=conversation_id
            )
            self.interaction_history.append(interaction)
            
            return {
                "success": True,
                "agent": agent_name,
                "action": action,
                "tool": tool_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing step {action} on agent {agent_name}: {e}")
            return {
                "success": False,
                "agent": agent_name,
                "action": action,
                "error": str(e)
            }

    async def coordinate_task(self, task_description: str, 
                            required_agents: Optional[List[str]] = None,
                            max_rounds: int = 10,
                            preserve_context: bool = True) -> Dict[str, Any]:
        """Coordinate a task across multiple agents with enhanced features"""
        
        if required_agents is None:
            required_agents = ["meta", "research", "signal", "execution"]
            
        # Create conversation for this task
        conversation_id = await self.initiate_conversation(
            topic=f"Task: {task_description[:50]}...",
            participants=required_agents,
            initial_message=task_description,
            context_data={"task_type": "coordination", "max_rounds": max_rounds}
        )
        
        # Create group chat for this task
        group_chat = self.group_chats[conversation_id]["group_chat"]
        
        try:
            # Initiate the conversation using the first agent as sender
            sender_agent = self.agents["meta"].get_agent()
            recipient_agent = self.agents["research"].get_agent()
            
            result = await sender_agent.a_initiate_chat(
                recipient=recipient_agent,
                message=task_description,
                max_rounds=max_rounds
            )
            
            # Update conversation context with results
            if preserve_context:
                self.conversation_contexts[conversation_id].context_data["task_result"] = result
            
            # Update performance metrics
            self._update_performance_metrics(task_description, result, conversation_id)
            
            return {
                "success": True,
                "result": str(result),
                "conversation_id": conversation_id,
                "agents_involved": required_agents,
                "rounds": 1,  # ChatResult doesn't have len()
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error coordinating task: {e}")
            return {
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id,
                "agents_involved": required_agents,
                "timestamp": datetime.now().isoformat()
            }

    def _update_performance_metrics(self, task_description: str, result: Any, conversation_id: str):
        """Update performance metrics for the task"""
        task_id = f"task_{len(self.interaction_history)}"
        self.performance_metrics[task_id] = {
            "task_description": task_description,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "success": result is not None,
            "rounds": 1,  # ChatResult doesn't have len()
            "agents_involved": len(self.agents)
        }

    def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation history and context"""
        if conversation_id not in self.conversation_contexts:
            return {"error": "Conversation not found"}
            
        context = self.conversation_contexts[conversation_id]
        return {
            "conversation_id": conversation_id,
            "topic": context.topic,
            "participants": context.participants,
            "messages": context.messages,
            "context_data": context.context_data,
            "created_at": context.created_at.isoformat(),
            "last_updated": context.last_updated.isoformat(),
            "message_count": len(context.messages)
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents with enhanced metrics"""
        status = {}
        for agent_name, agent in self.agents.items():
            # Get agent interactions
            agent_interactions = [
                i for i in self.interaction_history 
                if i.from_agent == agent_name or i.to_agent == agent_name
            ]
            
            status[agent_name] = {
                "name": agent_name,
                "tools_count": len(agent.tools),
                "memory_entries": len(agent.memory),
                "interactions_count": len(agent_interactions),
                "recent_interactions": [
                    {
                        "timestamp": i.timestamp.isoformat(),
                        "type": "outgoing" if i.from_agent == agent_name else "incoming",
                        "message": i.message[:100] + "..." if len(i.message) > 100 else i.message
                    }
                    for i in agent_interactions[-5:]  # Last 5 interactions
                ],
                "status": "active"
            }
        return status

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get enhanced performance metrics"""
        total_interactions = len(self.interaction_history)
        successful_tasks = sum(1 for m in self.performance_metrics.values() if m.get("success", False))
        
        # Calculate conversation metrics
        conversation_metrics = {
            "total_conversations": len(self.conversation_contexts),
            "active_conversations": len([c for c in self.conversation_contexts.values() 
                                       if (datetime.now() - c.last_updated).seconds < 3600]),  # Active in last hour
            "average_messages_per_conversation": sum(len(c.messages) for c in self.conversation_contexts.values()) / max(len(self.conversation_contexts), 1)
        }
        
        return {
            "total_interactions": total_interactions,
            "successful_tasks": successful_tasks,
            "total_tasks": len(self.performance_metrics),
            "success_rate": (successful_tasks / max(len(self.performance_metrics), 1)) * 100,
            "average_rounds": sum(m.get("rounds", 0) for m in self.performance_metrics.values()) / max(len(self.performance_metrics), 1),
            "conversation_metrics": conversation_metrics,
            "recent_tasks": list(self.performance_metrics.values())[-5:] if self.performance_metrics else [],
            "workflows_available": len(self.tool_workflows)
        }

    def get_mcp_tool_status(self) -> Dict[str, Any]:
        """Get MCP tool registry status with workflow information"""
        return {
            "total_tools": len(self.mcp_registry.list_all_tools()),
            "categories": self.mcp_registry.list_categories(),
            "tools_by_category": {
                category: len(self.mcp_registry.get_tools_by_category(category))
                for category in self.mcp_registry.list_categories()
            },
            "workflows": {
                workflow_id: {
                    "name": workflow.name,
                    "description": workflow.description,
                    "required_agents": workflow.required_agents,
                    "steps_count": len(workflow.steps)
                }
                for workflow_id, workflow in self.tool_workflows.items()
            }
        }

    async def test_agent_communication(self) -> Dict[str, Any]:
        """Test communication between agents with conversation management"""
        test_message = "Hello from coordinator! Please confirm you can receive and process messages."
        
        # Create a test conversation
        conversation_id = await self.initiate_conversation(
            topic="Communication Test",
            participants=list(self.agents.keys()),
            initial_message=test_message
        )
        
        results = {}
        for agent_name, agent in self.agents.items():
            try:
                # Send message to each agent
                message_result = await self.send_message(
                    conversation_id, 
                    "coordinator", 
                    f"Testing communication with {agent_name}",
                    {"test_type": "communication", "target_agent": agent_name}
                )
                
                # Simulate agent response
                response = f"Agent {agent_name} received message and is ready for collaboration"
                await self.send_message(
                    conversation_id,
                    agent_name,
                    response,
                    {"test_type": "response", "status": "ready"}
                )
                
                results[agent_name] = {
                    "status": "success",
                    "response": response,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                results[agent_name] = {
                    "status": "error",
                    "error": str(e),
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                }
                
        return {
            "test_type": "enhanced_communication",
            "conversation_id": conversation_id,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    async def test_mcp_tools(self) -> Dict[str, Any]:
        """Test MCP tool functionality with workflow execution"""
        test_results = {}
        
        # Test individual tools
        test_tools = [
            ("get_fear_greed_index", "research"),
            ("calculate_rsi", "analysis"),
            ("calculate_position_size", "risk_management")
        ]
        
        for tool_name, category in test_tools:
            tool = self.mcp_registry.get_tool(tool_name)
            if tool:
                try:
                    # Test with sample parameters
                    if tool_name == "get_fear_greed_index":
                        result = tool.function()
                    elif tool_name == "calculate_rsi":
                        result = tool.function([100, 101, 99, 102, 98], 14)
                    elif tool_name == "calculate_position_size":
                        result = tool.function(10000, 0.02, 0.05)
                    else:
                        result = {"status": "not_implemented"}
                        
                    test_results[tool_name] = {
                        "status": "success",
                        "result": result,
                        "category": category
                    }
                except Exception as e:
                    test_results[tool_name] = {
                        "status": "error",
                        "error": str(e),
                        "category": category
                    }
            else:
                test_results[tool_name] = {
                    "status": "not_found",
                    "category": category
                }
        
        # Test workflow execution
        workflow_test_result = await self.execute_tool_workflow(
            "market_analysis",
            {"symbol": "BTC/USDT", "timeframe": "1h"},
            conversation_id="workflow_test"
        )
        
        test_results["workflow_test"] = {
            "status": "success" if workflow_test_result["success"] else "error",
            "result": workflow_test_result,
            "type": "workflow_execution"
        }
                
        return {
            "test_type": "enhanced_mcp_tools",
            "results": test_results,
            "timestamp": datetime.now().isoformat()
        }

    async def execute_trading_workflow(self, symbol: str, action: str = "analyze") -> Dict[str, Any]:
        """Execute a complete trading workflow with enhanced coordination"""
        
        workflow_steps = []
        conversation_id = str(uuid.uuid4())
        
        if action == "analyze":
            # Execute market analysis workflow
            analysis_result = await self.execute_tool_workflow(
                "market_analysis",
                {"symbol": symbol, "timeframe": "1h"},
                conversation_id
            )
            workflow_steps.append({"phase": "market_analysis", "result": analysis_result})
            
            # Execute risk assessment workflow
            risk_result = await self.execute_tool_workflow(
                "risk_assessment",
                {"symbol": symbol, "account_balance": 10000, "risk_per_trade": 0.02},
                conversation_id
            )
            workflow_steps.append({"phase": "risk_assessment", "result": risk_result})
            
        elif action == "execute":
            # Full trading workflow with all phases
            workflow_steps = await self._execute_full_trading_workflow(symbol, conversation_id)
            
        return {
            "symbol": symbol,
            "action": action,
            "conversation_id": conversation_id,
            "workflow_steps": workflow_steps,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _execute_full_trading_workflow(self, symbol: str, conversation_id: str) -> List[Dict[str, Any]]:
        """Execute full trading workflow including execution with enhanced coordination"""
        workflow_steps = []
        
        # 1. Market Analysis
        analysis_result = await self.execute_tool_workflow(
            "market_analysis",
            {"symbol": symbol, "timeframe": "1h"},
            conversation_id
        )
        workflow_steps.append({"phase": "market_analysis", "result": analysis_result})
        
        # 2. Risk Assessment
        risk_result = await self.execute_tool_workflow(
            "risk_assessment",
            {"symbol": symbol, "account_balance": 10000, "risk_per_trade": 0.02},
            conversation_id
        )
        workflow_steps.append({"phase": "risk_assessment", "result": risk_result})
        
        # 3. Strategy Development
        strategy_task = f"Develop trading strategy for {symbol}"
        strategy_result = await self.coordinate_task(strategy_task, ["strategy", "meta"], preserve_context=True)
        workflow_steps.append({"phase": "strategy", "result": strategy_result})
        
        # 4. Trading Execution
        execution_result = await self.execute_tool_workflow(
            "trading_execution",
            {"symbol": symbol, "side": "buy", "quantity": 0.1},
            conversation_id
        )
        workflow_steps.append({"phase": "execution", "result": execution_result})
        
        return workflow_steps 