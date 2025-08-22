"""
VolexSwarm Agentic Framework

This module provides the foundation for transforming VolexSwarm agents
from simple FastAPI services into intelligent, autonomous AutoGen agents
with MCP tool integration.
"""

__version__ = "1.0.0"
__author__ = "VolexSwarm Team"

from .agent_templates import (
    ResearchAgent,
    SignalAgent,
    ExecutionAgent,
    StrategyAgent,
    RiskAgent,
    ComplianceAgent,
    MetaAgent,
    BacktestAgent,
    OptimizeAgent
)

from .mcp_tools import (
    MCPToolRegistry,
    ResearchTools,
    TradingTools,
    AnalysisTools,
    RiskManagementTools
)

from .agent_coordinator import EnhancedAgentCoordinator

__all__ = [
    # Agent Templates
    "ResearchAgent",
    "SignalAgent", 
    "ExecutionAgent",
    "StrategyAgent",
    "RiskAgent",
    "ComplianceAgent",
    "MetaAgent",
    "BacktestAgent",
    "OptimizeAgent",
    
    # MCP Tools
    "MCPToolRegistry",
    "ResearchTools",
    "TradingTools", 
    "AnalysisTools",
    "RiskManagementTools",
    
    # Coordination
    "EnhancedAgentCoordinator"
] 