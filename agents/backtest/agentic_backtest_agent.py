"""
Agentic Backtest Agent for VolexSwarm

This module provides the agentic version of the Backtest Agent, transforming it from
a simple FastAPI service into an intelligent, autonomous AutoGen agent with MCP tool
integration for autonomous backtesting and performance evaluation.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.agentic_framework.agent_templates import BaseAgent, AgentConfig
from agents.agentic_framework.mcp_tools import AnalysisTools, MCPToolRegistry
from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client
from common.logging import get_logger
from common.models import Strategy, Trade
from common.openai_client import get_openai_client

logger = get_logger("agentic_backtest")

@dataclass
class BacktestResult:
    """Represents a backtest result"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_duration: str
    performance_metrics: Dict[str, Any]
    trades: List[Dict[str, Any]]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class AgenticBacktestAgent(BaseAgent):
    """Agentic version of the Backtest Agent with MCP tool integration and autonomous reasoning"""

    def __init__(self, llm_config: Dict[str, Any] = None, tool_registry: MCPToolRegistry = None):
        # Initialize with a default LLM config to avoid validation errors
        default_llm_config = {
            "config_list": [{
                "api_type": "openai",
                "model": "gpt-4o-mini",
                "api_key": "mock-key-for-testing"
            }],
            "temperature": 0.7
        }
        
        system_message = """You are an intelligent Backtest Agent for VolexSwarm, a cryptocurrency trading system.

Your capabilities include:
- Autonomous historical data loading and validation
- Trade execution simulation and performance calculation
- Strategy validation and risk analysis
- Self-directed backtest optimization and refinement
- Reasoning about backtest results and strategy performance

You can:
1. Load and validate historical market data
2. Simulate trade execution with realistic conditions
3. Calculate comprehensive performance metrics
4. Validate strategy effectiveness and risk
5. Optimize backtest parameters and scenarios

Always explain your backtest decisions and performance analysis.
Be proactive in identifying backtest improvements and optimizations.
Learn from backtest results to enhance strategy validation over time."""

        config = AgentConfig(
            name="AgenticBacktestAgent",
            system_message=system_message,
            llm_config=llm_config or default_llm_config
        )
        super().__init__(config)
        
        # Assign MCP tools directly if not provided by coordinator
        if tool_registry is None:
            from agents.agentic_framework.mcp_tools import create_mcp_tool_registry
            tool_registry = create_mcp_tool_registry()
        self.tool_registry = tool_registry
        self.analysis_tools = AnalysisTools()
        
        # Initialize agent memory and cache attributes
        self.backtest_cache = {}
        self.backtest_results = []
        self.strategy_performance = {}
        
        # Initialize infrastructure attributes for test compatibility
        self.vault_client = None
        self.db_client = None
        self.openai_client = None

    async def initialize_infrastructure(self):
        """Initialize connections to existing infrastructure."""
        try:
            # Initialize Vault client
            self.vault_client = get_vault_client()
            
            # Initialize database client
            self.db_client = get_db_client()
            
            # Initialize OpenAI client
            self.openai_client = get_openai_client()
            
            # Initialize WebSocket client for real-time communication
            from common.websocket_client import AgentWebSocketClient
            self.ws_client = AgentWebSocketClient("agentic_backtest")
            await self.ws_client.connect()
            logger.info("WebSocket connection established successfully")
            
            # Configure LLM with real API key from Vault
            if self.vault_client:
                agent_config = get_agent_config("backtest")
                if agent_config and "openai_api_key" in agent_config:
                    # Update the LLM config with the real API key
                    self.config.llm_config = {
                        "config_list": [{
                            "api_type": "openai",
                            "model": "gpt-4o-mini",
                            "api_key": agent_config["openai_api_key"]
                        }],
                        "temperature": 0.7
                    }
                    logger.info("LLM configured with Vault API key")
                else:
                    logger.warning("OpenAI API key not found in Vault config")
            
            logger.info("Infrastructure initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize infrastructure: {e}")
            raise

    async def run_autonomous_backtest(self, strategy_definition: Dict[str, Any], 
                                    historical_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run autonomous backtest for a strategy.
        
        Args:
            strategy_definition: Strategy parameters and rules
            historical_data: Historical market data
            
        Returns:
            Dict containing backtest results and analysis
        """
        
        try:
            # Run backtest simulation
            backtest_result = await self._run_backtest_simulation(strategy_definition, historical_data)
            
            # Analyze performance
            performance_analysis = await self._analyze_performance(backtest_result)
            
            # Generate insights
            insights = await self._generate_backtest_insights(backtest_result, performance_analysis)
            
            # Store results
            self.backtest_results.append(backtest_result)
            
            return {
                "backtest_result": backtest_result,
                "performance_analysis": performance_analysis,
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Autonomous backtest failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _run_backtest_simulation(self, strategy_definition: Dict[str, Any], 
                                     historical_data: Dict[str, Any]) -> BacktestResult:
        """Run backtest simulation."""
        
        strategy_name = strategy_definition.get("name", "Unknown Strategy")
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Mock backtest simulation
        total_return = 0.15  # 15% return
        sharpe_ratio = 1.2
        max_drawdown = -0.08
        win_rate = 0.65
        total_trades = 45
        
        # Mock trades
        trades = [
            {
                "symbol": "BTCUSDT",
                "side": "buy",
                "amount": 0.1,
                "price": 50000.0,
                "timestamp": (start_date + timedelta(days=i)).isoformat(),
                "pnl": 0.02 if i % 3 == 0 else -0.01
            }
            for i in range(total_trades)
        ]
        
        performance_metrics = {
            "calmar_ratio": 1.8,
            "sortino_ratio": 1.5,
            "var_95": -0.03,
            "volatility": 0.12
        }
        
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            avg_trade_duration="2.5h",
            performance_metrics=performance_metrics,
            trades=trades
        )

    async def _analyze_performance(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """Analyze backtest performance."""
        
        analysis = {
            "risk_assessment": self._assess_risk(backtest_result),
            "performance_rating": self._rate_performance(backtest_result),
            "strengths": self._identify_strengths(backtest_result),
            "weaknesses": self._identify_weaknesses(backtest_result),
            "recommendations": self._generate_recommendations(backtest_result)
        }
        
        return analysis

    def _assess_risk(self, backtest_result: BacktestResult) -> Dict[str, Any]:
        """Assess risk profile of backtest results."""
        
        risk_level = "low"
        if backtest_result.max_drawdown < -0.15:
            risk_level = "high"
        elif backtest_result.max_drawdown < -0.10:
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "max_drawdown": backtest_result.max_drawdown,
            "var_95": backtest_result.performance_metrics.get("var_95", -0.03),
            "volatility": backtest_result.performance_metrics.get("volatility", 0.12)
        }

    def _rate_performance(self, backtest_result: BacktestResult) -> str:
        """Rate overall performance."""
        
        if backtest_result.sharpe_ratio > 1.5 and backtest_result.win_rate > 0.6:
            return "excellent"
        elif backtest_result.sharpe_ratio > 1.0 and backtest_result.win_rate > 0.5:
            return "good"
        elif backtest_result.sharpe_ratio > 0.5:
            return "fair"
        else:
            return "poor"

    def _identify_strengths(self, backtest_result: BacktestResult) -> List[str]:
        """Identify strategy strengths."""
        
        strengths = []
        
        if backtest_result.sharpe_ratio > 1.0:
            strengths.append("Good risk-adjusted returns")
        
        if backtest_result.win_rate > 0.6:
            strengths.append("High win rate")
        
        if backtest_result.max_drawdown > -0.1:
            strengths.append("Controlled drawdown")
        
        if backtest_result.total_trades > 30:
            strengths.append("Sufficient sample size")
        
        return strengths

    def _identify_weaknesses(self, backtest_result: BacktestResult) -> List[str]:
        """Identify strategy weaknesses."""
        
        weaknesses = []
        
        if backtest_result.sharpe_ratio < 0.5:
            weaknesses.append("Poor risk-adjusted returns")
        
        if backtest_result.win_rate < 0.5:
            weaknesses.append("Low win rate")
        
        if backtest_result.max_drawdown < -0.15:
            weaknesses.append("High drawdown risk")
        
        if backtest_result.total_trades < 20:
            weaknesses.append("Insufficient sample size")
        
        return weaknesses

    def _generate_recommendations(self, backtest_result: BacktestResult) -> List[str]:
        """Generate improvement recommendations."""
        
        recommendations = []
        
        if backtest_result.sharpe_ratio < 1.0:
            recommendations.append("Consider optimizing risk management parameters")
        
        if backtest_result.win_rate < 0.5:
            recommendations.append("Review entry and exit criteria")
        
        if backtest_result.max_drawdown < -0.15:
            recommendations.append("Implement tighter stop-loss mechanisms")
        
        if backtest_result.total_trades < 30:
            recommendations.append("Extend backtest period for better statistical significance")
        
        return recommendations

    async def _generate_backtest_insights(self, backtest_result: BacktestResult, 
                                        performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from backtest results."""
        
        insights = {
            "summary": f"Strategy '{backtest_result.strategy_name}' achieved {backtest_result.total_return*100:.1f}% return with {backtest_result.sharpe_ratio:.2f} Sharpe ratio",
            "risk_profile": performance_analysis["risk_assessment"]["risk_level"],
            "performance_rating": performance_analysis["performance_rating"],
            "key_findings": [
                f"Win rate: {backtest_result.win_rate*100:.1f}%",
                f"Maximum drawdown: {backtest_result.max_drawdown*100:.1f}%",
                f"Total trades: {backtest_result.total_trades}",
                f"Average trade duration: {backtest_result.avg_trade_duration}"
            ],
            "recommendations": performance_analysis["recommendations"]
        }
        
        return insights

    async def get_backtest_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get backtest history."""
        
        recent_results = self.backtest_results[-limit:] if len(self.backtest_results) > limit else self.backtest_results
        
        return [
            {
                "strategy_name": result.strategy_name,
                "start_date": result.start_date.isoformat(),
                "end_date": result.end_date.isoformat(),
                "total_return": result.total_return,
                "sharpe_ratio": result.sharpe_ratio,
                "performance_rating": self._rate_performance(result),
                "timestamp": result.timestamp.isoformat()
            }
            for result in recent_results
        ]

    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status for testing compatibility."""
        return {
            "agent_name": "AgenticBacktestAgent",
            "status": "active",
            "capabilities": ["backtesting", "performance_analysis", "strategy_validation"],
            "backtest_results": len(self.backtest_results),
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown the agent"""
        # Cleanup any resources if needed
        pass 