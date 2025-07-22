"""
VolexSwarm Configuration Agent - Trading Configuration and Cost Management
Handles trading budgets, API cost limits, and configuration management.
"""

import sys
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.websocket_client import AgentWebSocketClient, MessageType

# Initialize structured logger
logger = get_logger("config")

app = FastAPI(title="VolexSwarm Configuration Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients
vault_client = None
db_client = None
ws_client = None  # WebSocket client for real-time communication


class TradingBudgetConfig(BaseModel):
    """Trading budget configuration."""
    max_daily_spend: float = 1000.0  # Maximum daily trading spend in USD
    max_position_size: float = 100.0  # Maximum position size in USD
    max_total_positions: int = 10  # Maximum number of concurrent positions
    risk_per_trade: float = 0.02  # Maximum risk per trade (2%)


class OpenAIConfig(BaseModel):
    """OpenAI API configuration and limits."""
    max_daily_spend: float = 50.0  # Maximum daily spend on OpenAI API
    max_tokens_per_request: int = 4000  # Maximum tokens per request
    cost_per_1k_tokens: float = 0.002  # Cost per 1k tokens (GPT-3.5-turbo)
    enable_throttling: bool = True  # Enable automatic throttling when limits reached


class FeeConfig(BaseModel):
    """Trading fee configuration."""
    default_maker_fee: float = 0.001  # Default maker fee (0.1%)
    default_taker_fee: float = 0.001  # Default taker fee (0.1%)
    fee_currency: str = "USDT"
    include_fees_in_calculations: bool = True


class DualModeConfig(BaseModel):
    """Dual-mode trading configuration."""
    enabled: bool = False  # Enable dual-mode trading
    live_account: str = "binanceus"  # Live trading account
    dry_run_account: str = "binanceus_dry"  # Dry run account
    live_balance_limit: float = 1000.0  # Maximum live trading balance
    dry_run_balance: float = 10000.0  # Simulated dry run balance
    parallel_execution: bool = True  # Execute both modes simultaneously
    comparison_tracking: bool = True  # Track performance differences
    live_trade_percentage: float = 0.1  # Percentage of dry run size for live trades
    auto_adjust_live_size: bool = True  # Automatically adjust live trade sizes
    performance_threshold: float = 0.8  # Minimum performance ratio to increase live trading


class ConfigurationUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    config_type: str  # "trading_budget", "openai_limits", "fee_config"
    config_data: Dict[str, Any]
    description: Optional[str] = None


class APICostRequest(BaseModel):
    """Request model for tracking API costs."""
    service_name: str
    endpoint: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    request_id: Optional[str] = None
    agent_name: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class CostSummaryRequest(BaseModel):
    """Request model for cost summary."""
    service_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    agent_name: Optional[str] = None


class ConfigurationManager:
    """Manages trading configuration and cost tracking."""
    
    def __init__(self):
        self.default_configs = {
            "trading_budget": {
                "max_daily_spend": 1000.0,
                "max_position_size": 100.0,
                "max_total_positions": 10,
                "risk_per_trade": 0.02
            },
            "openai_limits": {
                "max_daily_spend": 50.0,
                "max_tokens_per_request": 4000,
                "cost_per_1k_tokens": 0.002,
                "enable_throttling": True
            },
            "fee_config": {
                "default_maker_fee": 0.001,
                "default_taker_fee": 0.001,
                "fee_currency": "USDT",
                "include_fees_in_calculations": True
            },
            "dual_mode_config": {
                "enabled": False,
                "live_account": "binanceus",
                "dry_run_account": "binanceus_dry",
                "live_balance_limit": 1000.0,
                "dry_run_balance": 10000.0,
                "parallel_execution": True,
                "comparison_tracking": True,
                "live_trade_percentage": 0.1,
                "auto_adjust_live_size": True,
                "performance_threshold": 0.8
            }
        }
    
    def get_config(self, key: str) -> Dict[str, Any]:
        """Get configuration value."""
        try:
            if not db_client:
                return self.default_configs.get(key, {})
            
            session = db_client.get_session()
            config = session.query(TradingConfiguration).filter(TradingConfiguration.key == key).first()
            
            if config:
                return config.value
            else:
                # Return default if not found
                return self.default_configs.get(key, {})
        except Exception as e:
            logger.error(f"Error getting config {key}: {str(e)}")
            return self.default_configs.get(key, {})
    
    def update_config(self, key: str, value: Dict[str, Any], description: str = None) -> bool:
        """Update configuration value."""
        try:
            if not db_client:
                logger.warning("Database not available, config update skipped")
                return False
            
            session = db_client.get_session()
            config = session.query(TradingConfiguration).filter(TradingConfiguration.key == key).first()
            
            if config:
                config.value = value
                config.description = description
                config.updated_at = datetime.utcnow()
                config.updated_by = "config_agent"
            else:
                config = TradingConfiguration(
                    key=key,
                    value=value,
                    description=description,
                    updated_by="config_agent"
                )
                session.add(config)
            
            session.commit()
            logger.info(f"Updated configuration {key}: {value}")
            return True
        except Exception as e:
            logger.error(f"Error updating config {key}: {str(e)}")
            return False
    
    def track_api_cost(self, cost_data: Dict[str, Any]) -> bool:
        """Track API cost usage."""
        try:
            if not db_client:
                logger.warning("Database not available, cost tracking skipped")
                return False
            
            session = db_client.get_session()
            cost_record = APICostTracking(
                timestamp=datetime.utcnow(),
                service_name=cost_data.get('service_name'),
                endpoint=cost_data.get('endpoint'),
                tokens_used=cost_data.get('tokens_used', 0),
                cost_usd=cost_data.get('cost_usd', 0.0),
                request_id=cost_data.get('request_id'),
                agent_name=cost_data.get('agent_name'),
                success=cost_data.get('success', True),
                error_message=cost_data.get('error_message')
            )
            
            session.add(cost_record)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error tracking API cost: {str(e)}")
            return False
    
    def get_cost_summary(self, service_name: str = None, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for the specified period."""
        try:
            if not db_client:
                return {"error": "Database not available"}
            
            session = db_client.get_session()
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = session.query(APICostTracking).filter(
                APICostTracking.timestamp >= start_date
            )
            
            if service_name:
                query = query.filter(APICostTracking.service_name == service_name)
            
            costs = query.all()
            
            # Calculate summaries
            total_cost = sum(cost.cost_usd for cost in costs)
            total_requests = len(costs)
            successful_requests = sum(1 for cost in costs if cost.success)
            total_tokens = sum(cost.tokens_used for cost in costs)
            
            # Group by service
            service_breakdown = {}
            for cost in costs:
                service = cost.service_name
                if service not in service_breakdown:
                    service_breakdown[service] = {
                        'total_cost': 0,
                        'total_requests': 0,
                        'successful_requests': 0,
                        'total_tokens': 0
                    }
                
                service_breakdown[service]['total_cost'] += cost.cost_usd
                service_breakdown[service]['total_requests'] += 1
                if cost.success:
                    service_breakdown[service]['successful_requests'] += 1
                service_breakdown[service]['total_tokens'] += cost.tokens_used
            
            return {
                'period_days': days,
                'start_date': start_date,
                'end_date': datetime.utcnow(),
                'total_cost': total_cost,
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
                'total_tokens': total_tokens,
                'service_breakdown': service_breakdown
            }
        except Exception as e:
            logger.error(f"Error getting cost summary: {str(e)}")
            return {"error": str(e)}
    
    def check_budget_limits(self, service_name: str, estimated_cost: float) -> Dict[str, Any]:
        """Check if a request would exceed budget limits."""
        try:
            if service_name == "openai":
                config = self.get_config("openai_limits")
                max_daily_spend = config.get('max_daily_spend', 50.0)
                
                # Get today's spending
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                if not db_client:
                    return {"can_proceed": True, "reason": "Database not available"}
                
                session = db_client.get_session()
                today_costs = session.query(APICostTracking).filter(
                    APICostTracking.service_name == "openai",
                    APICostTracking.timestamp >= today_start
                ).all()
                
                today_spent = sum(cost.cost_usd for cost in today_costs)
                would_exceed = (today_spent + estimated_cost) > max_daily_spend
                
                return {
                    "can_proceed": not would_exceed,
                    "today_spent": today_spent,
                    "max_daily_spend": max_daily_spend,
                    "estimated_cost": estimated_cost,
                    "would_exceed": would_exceed,
                    "remaining_budget": max_daily_spend - today_spent
                }
            
            return {"can_proceed": True, "reason": "No limits configured for this service"}
        except Exception as e:
            logger.error(f"Error checking budget limits: {str(e)}")
            return {"can_proceed": True, "reason": f"Error checking limits: {str(e)}"}


# Initialize configuration manager
config_manager = ConfigurationManager()


async def health_monitor_loop():
    """Background task to send periodic health updates to Meta Agent."""
    while True:
        try:
            if ws_client and ws_client.is_connected:
                # Gather health metrics
                health_data = {
                    "status": "healthy",
                    "db_connected": db_client is not None,
                    "vault_connected": vault_client is not None,
                    "config_management_active": True,
                    "last_health_check": datetime.utcnow().isoformat()
                }
                
                await ws_client.send_health_update(health_data)
                logger.debug("Sent health update to Meta Agent")
            
            # Wait 30 seconds before next health update
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
            await asyncio.sleep(30)  # Continue monitoring even if there's an error


@app.on_event("startup")
async def startup_event():
    """Initialize the configuration agent."""
    global vault_client, db_client, ws_client
    
    try:
        # Initialize Vault client
        vault_client = get_vault_client()
        logger.info("Vault client initialized")
        
        # Initialize database client
        db_client = get_db_client()
        logger.info("Database client initialized")
        
        # Initialize WebSocket client for real-time communication
        ws_client = AgentWebSocketClient("config")
        await ws_client.connect()
        logger.info("WebSocket client connected to Meta Agent")
        
        # Start health monitoring background task
        asyncio.create_task(health_monitor_loop())
        
        # Initialize default configurations if they don't exist
        for key, default_value in config_manager.default_configs.items():
            config_manager.update_config(key, default_value, f"Default {key} configuration")
        
        logger.info("Configuration agent started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize configuration agent: {str(e)}")
        raise


@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        db_healthy = db_health_check() if db_client else False
        
        return {
            "agent": "config",
            "status": "healthy",
            "timestamp": datetime.now(),
            "database": "healthy" if db_healthy else "unhealthy",
            "vault": "healthy" if vault_client else "unhealthy"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config/{config_key}")
def get_configuration(config_key: str):
    """Get configuration value."""
    try:
        config_value = config_manager.get_config(config_key)
        return {
            "agent": "config",
            "key": config_key,
            "value": config_value,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting configuration {config_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/update")
def update_configuration(request: ConfigurationUpdateRequest):
    """Update configuration value."""
    try:
        success = config_manager.update_config(
            request.config_type,
            request.config_data,
            request.description
        )
        
        if success:
            return {
                "agent": "config",
                "status": "success",
                "message": f"Configuration {request.config_type} updated successfully",
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cost/track")
def track_api_cost(request: APICostRequest):
    """Track API cost usage."""
    try:
        cost_data = {
            'service_name': request.service_name,
            'endpoint': request.endpoint,
            'tokens_used': request.tokens_used,
            'cost_usd': request.cost_usd,
            'request_id': request.request_id,
            'agent_name': request.agent_name,
            'success': request.success,
            'error_message': request.error_message
        }
        
        success = config_manager.track_api_cost(cost_data)
        
        if success:
            return {
                "agent": "config",
                "status": "success",
                "message": "API cost tracked successfully",
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to track API cost")
    except Exception as e:
        logger.error(f"Error tracking API cost: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cost/summary")
def get_cost_summary(service_name: str = None, days: int = 7):
    """Get cost summary for the specified period."""
    try:
        summary = config_manager.get_cost_summary(service_name, days)
        return {
            "agent": "config",
            "summary": summary,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting cost summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/budget/check")
def check_budget_limits(service_name: str, estimated_cost: float):
    """Check if a request would exceed budget limits."""
    try:
        result = config_manager.check_budget_limits(service_name, estimated_cost)
        return {
            "agent": "config",
            "service": service_name,
            "check_result": result,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error checking budget limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config/all")
def get_all_configurations():
    """Get all configuration values."""
    try:
        configs = {}
        for key in config_manager.default_configs.keys():
            configs[key] = config_manager.get_config(key)
        
        return {
            "agent": "config",
            "configurations": configs,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting all configurations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dual-mode/enable")
def enable_dual_mode():
    """Enable dual-mode trading."""
    try:
        dual_config = config_manager.get_config("dual_mode_config")
        dual_config["enabled"] = True
        
        success = config_manager.update_config(
            "dual_mode_config",
            dual_config,
            "Dual-mode trading enabled"
        )
        
        if success:
            return {
                "agent": "config",
                "status": "success",
                "message": "Dual-mode trading enabled successfully",
                "config": dual_config,
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to enable dual-mode")
    except Exception as e:
        logger.error(f"Error enabling dual-mode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dual-mode/disable")
def disable_dual_mode():
    """Disable dual-mode trading."""
    try:
        dual_config = config_manager.get_config("dual_mode_config")
        dual_config["enabled"] = False
        
        success = config_manager.update_config(
            "dual_mode_config",
            dual_config,
            "Dual-mode trading disabled"
        )
        
        if success:
            return {
                "agent": "config",
                "status": "success",
                "message": "Dual-mode trading disabled successfully",
                "config": dual_config,
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to disable dual-mode")
    except Exception as e:
        logger.error(f"Error disabling dual-mode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dual-mode/status")
def get_dual_mode_status():
    """Get dual-mode trading status and configuration."""
    try:
        dual_config = config_manager.get_config("dual_mode_config")
        
        return {
            "agent": "config",
            "dual_mode_enabled": dual_config.get("enabled", False),
            "configuration": dual_config,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting dual-mode status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012) 