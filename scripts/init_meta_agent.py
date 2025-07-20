#!/usr/bin/env python3
"""
Initialize Meta-Agent configuration in Vault.
"""

import os
import sys
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.vault import get_vault_client


def init_meta_agent():
    """Initialize Meta-Agent configuration in Vault."""
    
    try:
        vault_client = get_vault_client()
        
        # Meta-Agent configuration with coordination settings
        meta_config = {
            "autonomous_mode": True,  # Enable autonomous coordination
            "nlp_enabled": True,  # Enable natural language processing
            "coordination_enabled": True,  # Enable agent coordination
            "websocket_enabled": True,  # Enable real-time updates
            "agent_endpoints": {
                "research": "http://research:8000",
                "execution": "http://execution:8002",
                "signal": "http://signal:8003"
            },
            "nlp_settings": {
                "confidence_threshold": 0.7,
                "default_amount": 1000.0,
                "max_monitors": 10,
                "monitor_interval": 300  # 5 minutes
            },
            "coordination_settings": {
                "max_concurrent_trades": 3,
                "trade_timeout": 30,  # seconds
                "health_check_interval": 60,  # seconds
                "retry_attempts": 3
            },
            "autonomous_features": {
                "auto_coordination": True,
                "auto_monitoring": True,
                "auto_decision_making": True,
                "auto_risk_management": True,
                "auto_workflow_management": True
            },
            "workflow_settings": {
                "default_strategy": "autonomous_ai",
                "risk_level": "medium",
                "position_sizing": "dynamic",
                "stop_loss": 0.02,  # 2%
                "take_profit": 0.04  # 4%
            },
            "monitoring": {
                "log_all_commands": True,
                "log_coordination_events": True,
                "log_autonomous_decisions": True,
                "performance_tracking": True,
                "real_time_notifications": True
            }
        }
        
        # Store configuration in Vault
        vault_client.set_secret("agents/meta", meta_config)
        print("✅ Meta-Agent configuration stored in Vault")
        
        # Create autonomous workflow configuration
        autonomous_workflow = {
            "name": "Autonomous AI Workflow",
            "description": "Complete autonomous trading workflow coordinated by Meta-Agent",
            "steps": [
                {
                    "step": 1,
                    "agent": "research",
                    "action": "fetch_market_data",
                    "description": "Get current market data"
                },
                {
                    "step": 2,
                    "agent": "signal",
                    "action": "generate_signal",
                    "description": "Generate autonomous trading signal"
                },
                {
                    "step": 3,
                    "agent": "signal",
                    "action": "make_decision",
                    "description": "Make autonomous trading decision"
                },
                {
                    "step": 4,
                    "agent": "execution",
                    "action": "execute_trade",
                    "description": "Execute trade if decision is to trade"
                },
                {
                    "step": 5,
                    "agent": "meta",
                    "action": "monitor_results",
                    "description": "Monitor trade results and adjust"
                }
            ],
            "autonomous": True,
            "is_active": True,
            "coordination_features": {
                "agent_communication": True,
                "workflow_management": True,
                "error_handling": True,
                "performance_optimization": True
            }
        }
        
        vault_client.set_secret("workflows/autonomous_ai", autonomous_workflow)
        print("✅ Autonomous workflow configuration stored in Vault")
        
        print("\n🧠 Meta-Agent Configuration:")
        print(f"  - Autonomous mode: {meta_config['autonomous_mode']}")
        print(f"  - NLP enabled: {meta_config['nlp_enabled']}")
        print(f"  - Coordination enabled: {meta_config['coordination_enabled']}")
        print(f"  - WebSocket enabled: {meta_config['websocket_enabled']}")
        
        print("\n🤖 Coordination Features:")
        print(f"  - Auto coordination: {meta_config['autonomous_features']['auto_coordination']}")
        print(f"  - Auto monitoring: {meta_config['autonomous_features']['auto_monitoring']}")
        print(f"  - Auto decision making: {meta_config['autonomous_features']['auto_decision_making']}")
        print(f"  - Auto workflow management: {meta_config['autonomous_features']['auto_workflow_management']}")
        
        print("\n💬 Natural Language Commands:")
        print("  - 'analyze BTCUSD' - Analyze a symbol")
        print("  - 'trade BTCUSD if confident' - Execute autonomous trade")
        print("  - 'status' - Get system status")
        print("  - 'monitor ETHUSD' - Start autonomous monitoring")
        print("  - 'help' - Show available commands")
        
        print("\n🔄 Autonomous Workflow Steps:")
        for step in autonomous_workflow['steps']:
            print(f"  {step['step']}. {step['agent']} - {step['action']}: {step['description']}")
        
        print("\n⚠️  META-AGENT SAFETY NOTES:")
        print("  - Meta-Agent coordinates all autonomous AI agents")
        print("  - Natural language interface for human interaction")
        print("  - Real-time monitoring and coordination")
        print("  - Automatic workflow management")
        print("  - Complete autonomous trading system")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize Meta-Agent: {e}")
        return False


if __name__ == "__main__":
    print("Initializing Meta-Agent Configuration")
    print("=" * 50)
    
    if init_meta_agent():
        print("\n✅ Meta-Agent initialization completed successfully!")
        print("\n🧠 Meta-Agent Features:")
        print("  - Natural language command processing")
        print("  - Agent coordination and communication")
        print("  - Autonomous workflow management")
        print("  - Real-time monitoring and notifications")
        print("  - Complete system orchestration")
        
        print("\nNext steps:")
        print("1. Build and start the Meta-Agent: docker-compose up meta --build")
        print("2. Test the agent: curl http://localhost:8004/health")
        print("3. Test natural language: curl -X POST 'http://localhost:8004/command' -d 'analyze BTCUSD'")
        print("4. Test system status: curl http://localhost:8004/status")
        print("5. Test autonomous trade: curl -X POST 'http://localhost:8004/command' -d 'trade BTCUSD if confident'")
    else:
        print("\n❌ Meta-Agent initialization failed!")
        sys.exit(1) 