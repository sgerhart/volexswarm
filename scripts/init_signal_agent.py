#!/usr/bin/env python3
"""
Initialize autonomous AI signal agent configuration in Vault.
"""

import os
import sys
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.vault import get_vault_client


def init_signal_agent():
    """Initialize autonomous AI signal agent configuration in Vault."""
    
    try:
        vault_client = get_vault_client()
        
        # Signal agent configuration with autonomous AI settings
        signal_config = {
            "autonomous_mode": True,  # Enable autonomous decision making
            "ml_enabled": True,  # Enable machine learning models
            "confidence_threshold": 0.7,  # Minimum confidence for autonomous decisions
            "max_positions": 3,  # Maximum concurrent positions
            "position_sizing": 0.1,  # Position size as fraction of portfolio
            "technical_indicators": {
                "rsi_period": 14,
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "bollinger_period": 20,
                "bollinger_std": 2.0,
                "stochastic_period": 14
            },
            "ml_settings": {
                "model_type": "random_forest",
                "n_estimators": 100,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
                "random_state": 42
            },
            "risk_management": {
                "max_daily_loss": 0.05,  # 5% max daily loss
                "max_position_size": 0.2,  # 20% max position size
                "stop_loss": 0.02,  # 2% stop loss
                "take_profit": 0.04  # 4% take profit
            },
            "autonomous_features": {
                "auto_train_models": True,
                "auto_retrain_interval": 7,  # days
                "auto_signal_generation": True,
                "auto_decision_making": True,
                "auto_risk_adjustment": True
            },
            "monitoring": {
                "log_all_signals": True,
                "log_ml_predictions": True,
                "log_autonomous_decisions": True,
                "performance_tracking": True
            }
        }
        
        # Store configuration in Vault
        vault_client.set_secret("agents/signal", signal_config)
        print("✅ Autonomous AI signal agent configuration stored in Vault")
        
        # Create autonomous trading strategy
        autonomous_strategy = {
            "name": "Autonomous AI Strategy",
            "description": "Fully autonomous AI-driven trading strategy using ML and technical analysis",
            "agent_name": "signal",
            "autonomous": True,
            "parameters": {
                "symbols": ["BTCUSD", "ETHUSD", "ADAUSD"],
                "timeframes": ["1h", "4h", "1d"],
                "ml_models": ["random_forest", "gradient_boosting"],
                "technical_indicators": ["rsi", "macd", "bollinger_bands", "stochastic"],
                "risk_management": {
                    "position_sizing": "kelly_criterion",
                    "stop_loss": "dynamic",
                    "take_profit": "trailing"
                }
            },
            "is_active": True,
            "autonomous_features": {
                "self_learning": True,
                "adaptive_parameters": True,
                "market_regime_detection": True,
                "sentiment_analysis": True
            }
        }
        
        vault_client.set_secret("strategies/autonomous_ai", autonomous_strategy)
        print("✅ Autonomous AI strategy configuration stored in Vault")
        
        print("\n🤖 Autonomous AI Signal Agent Configuration:")
        print(f"  - Autonomous mode: {signal_config['autonomous_mode']}")
        print(f"  - ML enabled: {signal_config['ml_enabled']}")
        print(f"  - Confidence threshold: {signal_config['confidence_threshold']}")
        print(f"  - Max positions: {signal_config['max_positions']}")
        print(f"  - Position sizing: {signal_config['position_sizing']}")
        
        print("\n🧠 AI Features:")
        print(f"  - Auto train models: {signal_config['autonomous_features']['auto_train_models']}")
        print(f"  - Auto signal generation: {signal_config['autonomous_features']['auto_signal_generation']}")
        print(f"  - Auto decision making: {signal_config['autonomous_features']['auto_decision_making']}")
        print(f"  - Auto risk adjustment: {signal_config['autonomous_features']['auto_risk_adjustment']}")
        
        print("\n📊 Technical Indicators:")
        for indicator, value in signal_config['technical_indicators'].items():
            print(f"  - {indicator}: {value}")
        
        print("\n⚠️  AUTONOMOUS AI SAFETY NOTES:")
        print("  - AI agents can make autonomous trading decisions")
        print("  - All decisions are logged and auditable")
        print("  - Risk management limits are enforced")
        print("  - Models are continuously learning and adapting")
        print("  - Human oversight recommended for production use")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize autonomous AI signal agent: {e}")
        return False


if __name__ == "__main__":
    print("Initializing Autonomous AI Signal Agent Configuration")
    print("=" * 60)
    
    if init_signal_agent():
        print("\n✅ Autonomous AI signal agent initialization completed successfully!")
        print("\n🤖 AI Agent Features:")
        print("  - Autonomous decision making")
        print("  - Machine learning model training")
        print("  - Technical analysis indicators")
        print("  - Risk management automation")
        print("  - Self-learning capabilities")
        
        print("\nNext steps:")
        print("1. Build and start the signal agent: docker-compose up signal --build")
        print("2. Test the agent: curl http://localhost:8003/health")
        print("3. Train ML model: curl -X POST 'http://localhost:8003/models/train?symbol=BTCUSD'")
        print("4. Generate autonomous signal: curl -X POST 'http://localhost:8003/signals/generate?symbol=BTCUSD'")
        print("5. Get AI insights: curl http://localhost:8003/autonomous/insights/BTCUSD")
        print("6. Make autonomous decision: curl -X POST 'http://localhost:8003/autonomous/decide?symbol=BTCUSD'")
    else:
        print("\n❌ Autonomous AI signal agent initialization failed!")
        sys.exit(1) 