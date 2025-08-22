"""
Agentic Monitor Agent for VolexSwarm

This module provides the agentic version of the Monitor Agent, transforming it from
a simple FastAPI service into an intelligent, autonomous AutoGen agent with MCP tool
integration for autonomous system monitoring and health management.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import json
import psutil
import numpy as np
import pandas as pd

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.agentic_framework.agent_templates import BaseAgent, AgentConfig
from agents.agentic_framework.mcp_tools import AnalysisTools, MCPToolRegistry
from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client
from common.logging import get_logger
from common.models import SystemConfig, AgentLog
from common.openai_client import get_openai_client

logger = get_logger("agentic_monitor")

@dataclass
class SystemMetrics:
    """Represents system monitoring metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    agent_health: Dict[str, str]
    database_health: str
    vault_health: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class Alert:
    """Represents a system alert"""
    alert_id: str
    alert_type: str
    severity: str
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MonitoringManager:
    """Manages system monitoring and alerting"""
    
    def __init__(self):
        self.metrics_history = []
        self.alerts_history = []
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'database_connections': 100,
            'response_time': 2.0
        }
        
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Active connections
            connections = len(psutil.net_connections())
            
            # Mock agent health (in real implementation, this would check actual agents)
            agent_health = {
                'research': 'healthy',
                'signal': 'healthy',
                'execution': 'healthy',
                'strategy': 'healthy',
                'risk': 'healthy',
                'compliance': 'healthy',
                'backtest': 'healthy',
                'optimize': 'healthy',
                'meta': 'healthy'
            }
            
            # Mock database and vault health
            database_health = 'healthy'
            vault_health = 'healthy'
            
            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=connections,
                agent_health=agent_health,
                database_health=database_health,
                vault_health=vault_health
            )
            
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise
    
    def check_alerts(self, metrics: SystemMetrics) -> List[Alert]:
        """Check for alerts based on current metrics"""
        alerts = []
        
        try:
            # CPU usage alert
            if metrics.cpu_usage > self.alert_thresholds['cpu_usage']:
                alerts.append(Alert(
                    alert_id=f"cpu_alert_{datetime.now().timestamp()}",
                    alert_type="high_cpu_usage",
                    severity="warning" if metrics.cpu_usage < 95 else "critical",
                    message=f"CPU usage is {metrics.cpu_usage:.1f}% (threshold: {self.alert_thresholds['cpu_usage']}%)",
                    metric_value=metrics.cpu_usage,
                    threshold=self.alert_thresholds['cpu_usage']
                ))
            
            # Memory usage alert
            if metrics.memory_usage > self.alert_thresholds['memory_usage']:
                alerts.append(Alert(
                    alert_id=f"memory_alert_{datetime.now().timestamp()}",
                    alert_type="high_memory_usage",
                    severity="warning" if metrics.memory_usage < 95 else "critical",
                    message=f"Memory usage is {metrics.memory_usage:.1f}% (threshold: {self.alert_thresholds['memory_usage']}%)",
                    metric_value=metrics.memory_usage,
                    threshold=self.alert_thresholds['memory_usage']
                ))
            
            # Disk usage alert
            if metrics.disk_usage > self.alert_thresholds['disk_usage']:
                alerts.append(Alert(
                    alert_id=f"disk_alert_{datetime.now().timestamp()}",
                    alert_type="high_disk_usage",
                    severity="warning" if metrics.disk_usage < 98 else "critical",
                    message=f"Disk usage is {metrics.disk_usage:.1f}% (threshold: {self.alert_thresholds['disk_usage']}%)",
                    metric_value=metrics.disk_usage,
                    threshold=self.alert_thresholds['disk_usage']
                ))
            
            # Database connections alert
            if metrics.active_connections > self.alert_thresholds['database_connections']:
                alerts.append(Alert(
                    alert_id=f"connections_alert_{datetime.now().timestamp()}",
                    alert_type="high_connection_count",
                    severity="warning",
                    message=f"Active connections: {metrics.active_connections} (threshold: {self.alert_thresholds['database_connections']})",
                    metric_value=metrics.active_connections,
                    threshold=self.alert_thresholds['database_connections']
                ))
            
            # Agent health alerts
            for agent_name, health_status in metrics.agent_health.items():
                if health_status != 'healthy':
                    alerts.append(Alert(
                        alert_id=f"agent_alert_{agent_name}_{datetime.now().timestamp()}",
                        alert_type="agent_unhealthy",
                        severity="critical" if health_status == 'down' else "warning",
                        message=f"Agent {agent_name} is {health_status}",
                        metric_value=0 if health_status == 'down' else 1,
                        threshold=1
                    ))
            
            # Add alerts to history
            self.alerts_history.extend(alerts)
            
            # Keep only last 1000 alerts
            if len(self.alerts_history) > 1000:
                self.alerts_history = self.alerts_history[-1000:]
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
            return []
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for the specified time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
            
            if not recent_metrics:
                return {"error": "No metrics available for the specified time period"}
            
            # Calculate statistics
            cpu_values = [m.cpu_usage for m in recent_metrics]
            memory_values = [m.memory_usage for m in recent_metrics]
            disk_values = [m.disk_usage for m in recent_metrics]
            
            summary = {
                "time_period_hours": hours,
                "metrics_count": len(recent_metrics),
                "cpu": {
                    "average": np.mean(cpu_values),
                    "max": np.max(cpu_values),
                    "min": np.min(cpu_values),
                    "std": np.std(cpu_values)
                },
                "memory": {
                    "average": np.mean(memory_values),
                    "max": np.max(memory_values),
                    "min": np.min(memory_values),
                    "std": np.std(memory_values)
                },
                "disk": {
                    "average": np.mean(disk_values),
                    "max": np.max(disk_values),
                    "min": np.min(disk_values),
                    "std": np.std(disk_values)
                },
                "alerts_count": len([a for a in self.alerts_history if a.timestamp > cutoff_time]),
                "current_status": "healthy" if not recent_metrics[-1].cpu_usage > 80 else "warning"
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {"error": str(e)}
    
    def update_alert_thresholds(self, new_thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Update alert thresholds"""
        try:
            for key, value in new_thresholds.items():
                if key in self.alert_thresholds:
                    self.alert_thresholds[key] = value
            
            return {
                "status": "success",
                "updated_thresholds": self.alert_thresholds,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update alert thresholds: {e}")
            return {"error": str(e)}

class AgenticMonitorAgent(BaseAgent):
    """Agentic version of the Monitor Agent with MCP tool integration and autonomous reasoning"""

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
        
        system_message = """You are an intelligent Monitor Agent for VolexSwarm, a cryptocurrency trading system.

Your capabilities include:
- Autonomous system health monitoring and performance tracking
- Real-time alert generation and threshold management
- Resource utilization analysis and optimization recommendations
- Self-directed monitoring strategy development and refinement
- Reasoning about system performance and health trends

You can:
1. Monitor CPU, memory, disk, and network usage
2. Track agent health and database connectivity
3. Generate alerts for performance issues
4. Analyze system performance trends
5. Recommend system optimizations
6. Manage alert thresholds dynamically

Always explain your monitoring decisions and performance analysis.
Be proactive in identifying potential issues and optimization opportunities.
Learn from monitoring data to enhance system performance over time."""

        config = AgentConfig(
            name="AgenticMonitorAgent",
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
        
        # Initialize monitoring manager
        self.monitoring_manager = MonitoringManager()
        
        # Initialize agent memory and cache attributes
        self.monitoring_cache = {}
        self.alert_history = []
        self.performance_trends = {}
        
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
            self.ws_client = AgentWebSocketClient("agentic_monitor")
            await self.ws_client.connect()
            logger.info("WebSocket connection established successfully")
            
            # Configure LLM with real API key from Vault
            if self.vault_client:
                # Get agent-specific config
                agent_config = get_agent_config("monitor")
                
                # Get OpenAI API key from the correct location
                openai_secret = self.vault_client.get_secret("openai/api_key")
                openai_api_key = None
                if openai_secret and "api_key" in openai_secret:
                    openai_api_key = openai_secret["api_key"]
                
                if openai_api_key:
                    # Update the LLM config with the real API key
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
            
            logger.info("Infrastructure initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize infrastructure: {e}")
            raise

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            metrics = self.monitoring_manager.collect_system_metrics()
            
            return {
                'status': 'success',
                'metrics': {
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'disk_usage': metrics.disk_usage,
                    'network_io': metrics.network_io,
                    'active_connections': metrics.active_connections,
                    'agent_health': metrics.agent_health,
                    'database_health': metrics.database_health,
                    'vault_health': metrics.vault_health,
                    'timestamp': metrics.timestamp.isoformat()
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def check_system_alerts(self) -> Dict[str, Any]:
        """Check for system alerts"""
        try:
            metrics = self.monitoring_manager.collect_system_metrics()
            alerts = self.monitoring_manager.check_alerts(metrics)
            
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    'alert_id': alert.alert_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'metric_value': alert.metric_value,
                    'threshold': alert.threshold,
                    'timestamp': alert.timestamp.isoformat()
                })
            
            return {
                'status': 'success',
                'alerts': alert_data,
                'alerts_count': len(alerts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to check system alerts: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_system_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance summary"""
        try:
            summary = self.monitoring_manager.get_metrics_summary(hours)
            
            return {
                'status': 'success',
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system summary: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def update_monitoring_thresholds(self, new_thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Update monitoring thresholds"""
        try:
            result = self.monitoring_manager.update_alert_thresholds(new_thresholds)
            
            return {
                'status': 'success',
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update monitoring thresholds: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_monitoring_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get monitoring history"""
        try:
            history = []
            for metrics in self.monitoring_manager.metrics_history[-limit:]:
                history.append({
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'disk_usage': metrics.disk_usage,
                    'active_connections': metrics.active_connections,
                    'timestamp': metrics.timestamp.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get monitoring history: {e}")
            return []

    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status for testing compatibility."""
        return {
            "agent_name": "AgenticMonitorAgent",
            "status": "active",
            "capabilities": ["system_monitoring", "alert_generation", "performance_analysis"],
            "metrics_history_count": len(self.monitoring_manager.metrics_history),
            "alerts_history_count": len(self.monitoring_manager.alerts_history),
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown the agent"""
        # Cleanup any resources if needed
        pass 