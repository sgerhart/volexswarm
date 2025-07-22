"""
Conversational AI Module for VolexSwarm Phase 3
Advanced natural language processing with GPT-4 integration for sophisticated trading conversations.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from .openai_client import VolexSwarmOpenAIClient
from .logging import get_logger

logger = get_logger("conversational_ai")


class TaskType(Enum):
    """Types of tasks that can be decomposed from conversations."""
    ACCOUNT_CHECK = "account_check"
    MARKET_RESEARCH = "market_research"
    TECHNICAL_ANALYSIS = "technical_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    TRADE_EXECUTION = "trade_execution"
    STRATEGY_OPTIMIZATION = "strategy_optimization"
    PORTFOLIO_MONITORING = "portfolio_monitoring"
    COMPLIANCE_CHECK = "compliance_check"


class TaskStatus(Enum):
    """Status of individual tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Individual task in a conversation workflow."""
    id: str
    type: TaskType
    description: str
    agent: str
    parameters: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ConversationContext:
    """Maintains context throughout a conversation."""
    conversation_id: str
    user_id: str
    session_start: datetime
    last_interaction: datetime
    user_preferences: Dict[str, Any]
    trading_context: Dict[str, Any]  # Budget, risk tolerance, goals
    conversation_history: List[Dict[str, Any]]
    active_tasks: List[Task]
    completed_tasks: List[Task]
    
    def __post_init__(self):
        if not self.user_preferences:
            self.user_preferences = {}
        if not self.trading_context:
            self.trading_context = {}
        if not self.conversation_history:
            self.conversation_history = []
        if not self.active_tasks:
            self.active_tasks = []
        if not self.completed_tasks:
            self.completed_tasks = []


@dataclass
class ConversationResponse:
    """Response from the conversational AI system."""
    message: str
    tasks: List[Task]
    requires_confirmation: bool = False
    structured_data: Optional[Dict[str, Any]] = None
    next_actions: List[str] = None
    context_updates: Dict[str, Any] = None

    def __post_init__(self):
        if not self.next_actions:
            self.next_actions = []
        if not self.context_updates:
            self.context_updates = {}


class ConversationalAI:
    """Advanced conversational AI for VolexSwarm trading interactions."""
    
    def __init__(self):
        self.openai_client = VolexSwarmOpenAIClient()
        self.active_conversations: Dict[str, ConversationContext] = {}
        
        # System prompts for different conversation types
        self.system_prompts = {
            "trading_assistant": """You are VolexSwarm, an advanced AI trading assistant. You help users with cryptocurrency trading by:

1. Understanding complex multi-step trading instructions
2. Breaking down requests into specific tasks for specialized agents
3. Coordinating research, analysis, risk assessment, and execution
4. Providing clear explanations and seeking confirmation for important decisions
5. Maintaining context across conversations

You have access to these specialized agents:
- Research Agent: Market analysis, news sentiment, trend detection
- Signal Agent: Technical analysis, ML predictions, trading signals
- Execution Agent: Order placement, position tracking, balance checking
- Risk Agent: Position sizing, risk assessment, stop-loss management
- Strategy Agent: Strategy development and optimization
- Compliance Agent: Trade logging and regulatory compliance

When users give you complex instructions like "I have $200 in Binance, research the best tokens and trade for highest returns", you should:
1. Break this into specific tasks
2. Explain your planned approach
3. Ask for confirmation if needed
4. Execute tasks in logical order
5. Provide updates as tasks complete

Always be helpful, clear, and focused on maximizing trading success while managing risk.""",

            "task_decomposer": """You are a task decomposition specialist. Given a complex trading instruction, break it down into specific, actionable tasks.

Available task types and their assigned agents:
- account_check → "execution" agent: Verify account balance and available funds
- market_research → "research" agent: Research market conditions, trending tokens, news analysis
- technical_analysis → "signal" agent: Perform technical analysis on specific symbols
- risk_assessment → "risk" agent: Assess position sizing and risk parameters
- trade_execution → "execution" agent: Execute buy/sell orders
- strategy_optimization → "strategy" agent: Optimize trading strategies
- portfolio_monitoring → "monitor" agent: Monitor existing positions
- compliance_check → "compliance" agent: Ensure regulatory compliance

CRITICAL: Use the exact agent names shown above (research, signal, execution, risk, strategy, monitor, compliance).

For each task, specify:
- Task type (from list above)
- Description (clear, actionable description)
- Agent (exact agent name from mapping above)
- Parameters (relevant data for the task)

Return your response as JSON with a 'tasks' array."""
        }
    
    def get_or_create_conversation(self, user_id: str, conversation_id: Optional[str] = None) -> ConversationContext:
        """Get existing conversation or create new one."""
        if conversation_id and conversation_id in self.active_conversations:
            context = self.active_conversations[conversation_id]
            context.last_interaction = datetime.utcnow()
            return context
        
        # Create new conversation
        new_id = conversation_id or str(uuid.uuid4())
        context = ConversationContext(
            conversation_id=new_id,
            user_id=user_id,
            session_start=datetime.utcnow(),
            last_interaction=datetime.utcnow(),
            user_preferences={},
            trading_context={},
            conversation_history=[],
            active_tasks=[],
            completed_tasks=[]
        )
        
        self.active_conversations[new_id] = context
        return context
    
    async def process_message(self, user_message: str, user_id: str, conversation_id: Optional[str] = None) -> ConversationResponse:
        """Process a user message and generate appropriate response and tasks."""
        try:
            # Get or create conversation context
            context = self.get_or_create_conversation(user_id, conversation_id)
            
            # Add user message to history
            context.conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Generate response using GPT-4
            response = await self._generate_response(user_message, context)
            
            # Add AI response to history
            context.conversation_history.append({
                "role": "assistant",
                "content": response.message,
                "timestamp": datetime.utcnow().isoformat(),
                "tasks": [asdict(task) for task in response.tasks] if response.tasks else []
            })
            
            # Add tasks to context
            context.active_tasks.extend(response.tasks)
            
            # Update context with any changes
            if response.context_updates:
                for key, value in response.context_updates.items():
                    if key == "trading_context":
                        context.trading_context.update(value)
                    elif key == "user_preferences":
                        context.user_preferences.update(value)
            
            logger.info(f"Processed message for conversation {context.conversation_id}", {
                "user_message": user_message,
                "response_tasks": len(response.tasks),
                "requires_confirmation": response.requires_confirmation
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return ConversationResponse(
                message=f"I encountered an error processing your request: {str(e)}. Please try again.",
                tasks=[],
                requires_confirmation=False
            )
    
    async def _generate_response(self, user_message: str, context: ConversationContext) -> ConversationResponse:
        """Generate response using GPT-4 with conversation context."""
        try:
            # Prepare conversation context for GPT
            messages = [
                {"role": "system", "content": self.system_prompts["trading_assistant"]}
            ]
            
            # Add relevant conversation history (last 10 messages to avoid token limits)
            recent_history = context.conversation_history[-10:] if context.conversation_history else []
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Add context information
            context_prompt = f"""
Current Context:
- User ID: {context.user_id}
- Trading Context: {json.dumps(context.trading_context, indent=2)}
- Active Tasks: {len(context.active_tasks)}
- User Preferences: {json.dumps(context.user_preferences, indent=2)}

Please respond naturally and break down complex requests into specific tasks if needed.
"""
            messages.append({"role": "system", "content": context_prompt})
            
            # Generate response
            response = await self.openai_client.generate_completion(
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Check if we need to decompose tasks
            tasks = []
            requires_confirmation = False
            
            if self._should_decompose_tasks(user_message):
                tasks = await self._decompose_tasks(user_message, context)
                requires_confirmation = self._requires_confirmation(user_message, tasks)
            
            return ConversationResponse(
                message=response,
                tasks=tasks,
                requires_confirmation=requires_confirmation,
                context_updates=self._extract_context_updates(user_message)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return ConversationResponse(
                message="I'm having trouble processing your request right now. Please try again in a moment.",
                tasks=[]
            )
    
    def _should_decompose_tasks(self, message: str) -> bool:
        """Determine if message requires task decomposition."""
        task_indicators = [
            "research", "analyze", "trade", "buy", "sell", "invest",
            "find", "best", "profitable", "strategy", "portfolio",
            "monitor", "track", "optimize", "balance", "account"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in task_indicators)
    
    async def _decompose_tasks(self, user_message: str, context: ConversationContext) -> List[Task]:
        """Decompose complex message into specific tasks."""
        try:
            decomposition_prompt = f"""
User Request: "{user_message}"

Current Trading Context: {json.dumps(context.trading_context, indent=2)}

Break this request into specific, actionable tasks. Consider the full workflow needed to complete the user's request.

{self.system_prompts["task_decomposer"]}

IMPORTANT: Return ONLY a valid JSON object with this exact structure:
{{
  "tasks": [
    {{
      "type": "market_research",
      "description": "Task description",
      "agent": "research",
      "parameters": {{}}
    }}
  ]
}}

Do not include any other text, explanations, or formatting. Return only the JSON."""
            
            response = await self.openai_client.generate_completion(
                messages=[
                    {"role": "system", "content": decomposition_prompt},
                    {"role": "user", "content": f"Decompose this request: {user_message}"}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            # Parse the response to extract tasks
            try:
                # Try to extract JSON from the response if it's embedded in text
                response_text = response.strip()
                
                # If response starts with ```json, extract the JSON content
                if response_text.startswith("```json"):
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    if end != -1:
                        response_text = response_text[start:end].strip()
                elif response_text.startswith("```"):
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    if end != -1:
                        response_text = response_text[start:end].strip()
                
                # Try to find JSON object in the text
                if not response_text.startswith("{"):
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        response_text = response_text[json_start:json_end]
                
                logger.info(f"Attempting to parse task decomposition: {response_text[:200]}...")
                task_data = json.loads(response_text)
                tasks = []
                
                for task_info in task_data.get("tasks", []):
                    try:
                        task = Task(
                            id=str(uuid.uuid4()),
                            type=TaskType(task_info["type"]),
                            description=task_info["description"],
                            agent=task_info["agent"],
                            parameters=task_info.get("parameters", {})
                        )
                        tasks.append(task)
                        logger.info(f"Created task: {task.type} for {task.agent}")
                    except (KeyError, ValueError) as task_error:
                        logger.warning(f"Failed to create task from {task_info}: {task_error}")
                        continue
                
                logger.info(f"Successfully created {len(tasks)} tasks from decomposition")
                return tasks
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse task decomposition: {e}")
                logger.error(f"Raw response was: {response[:500]}...")
                return []
                
        except Exception as e:
            logger.error(f"Failed to decompose tasks: {e}")
            return []
    
    def _requires_confirmation(self, message: str, tasks: List[Task]) -> bool:
        """Determine if tasks require user confirmation before execution."""
        high_risk_tasks = [TaskType.TRADE_EXECUTION]
        has_trading_amount = any(word in message.lower() for word in ["$", "usd", "trade", "buy", "sell"])
        has_high_risk_tasks = any(task.type in high_risk_tasks for task in tasks)
        
        return has_trading_amount or has_high_risk_tasks or len(tasks) > 3
    
    def _extract_context_updates(self, message: str) -> Dict[str, Any]:
        """Extract context updates from user message."""
        updates = {}
        message_lower = message.lower()
        
        # Extract budget information
        import re
        budget_match = re.search(r'\$(\d+(?:\.\d{2})?)', message)
        if budget_match:
            budget = float(budget_match.group(1))
            updates["trading_context"] = {"budget": budget}
        
        # Extract risk preferences
        if any(word in message_lower for word in ["conservative", "safe", "low risk"]):
            updates["user_preferences"] = {"risk_tolerance": "low"}
        elif any(word in message_lower for word in ["aggressive", "high risk", "risky"]):
            updates["user_preferences"] = {"risk_tolerance": "high"}
        
        return updates
    
    def update_task_status(self, conversation_id: str, task_id: str, status: TaskStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Update the status of a task."""
        if conversation_id not in self.active_conversations:
            return
        
        context = self.active_conversations[conversation_id]
        
        # Find and update the task
        for task in context.active_tasks:
            if task.id == task_id:
                task.status = status
                if result:
                    task.result = result
                if error:
                    task.error = error
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = datetime.utcnow()
                    context.completed_tasks.append(task)
                    context.active_tasks.remove(task)
                break
    
    def get_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context by ID."""
        return self.active_conversations.get(conversation_id)
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up old conversation contexts."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        expired_conversations = [
            conv_id for conv_id, context in self.active_conversations.items()
            if context.last_interaction < cutoff_time
        ]
        
        for conv_id in expired_conversations:
            del self.active_conversations[conv_id]
            
        if expired_conversations:
            logger.info(f"Cleaned up {len(expired_conversations)} expired conversations") 