"""
Dynamic Configuration Manager for VolexSwarm

This module provides database-driven configuration management to replace all hardcoded
static values in the trading system. All configuration is loaded from the database
and can be updated dynamically without code changes.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass
from sqlalchemy import text

from common.db import get_db_client
from common.logging import get_logger

logger = get_logger("config_manager")

class SignalType(Enum):
    """Types of trading signals."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"
    WATCH = "WATCH"

class SignalPriority(Enum):
    """Signal priority levels for real-time processing."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5

class TradingMode(Enum):
    """Trading system operation modes."""
    SIMULATION = "simulation"           # Safe testing with fake orders
    REAL_TRADING = "real_trading"      # Live trading with real money
    HYBRID = "hybrid"                  # Both simulation and real trading
    SANDBOX = "sandbox"                # Strategy testing environment
    BACKTEST = "backtest"              # Historical strategy testing

@dataclass
class TradingConfig:
    """Trading configuration settings."""
    mode: TradingMode
    simulation_balance: float = 10000.0  # Starting balance for simulation
    max_simulation_risk: float = 0.02    # 2% max risk per trade in simulation
    real_trading_enabled: bool = False   # Whether real trading is allowed
    simulation_accounts: List[str] = None  # List of simulation account names
    real_accounts: List[str] = None       # List of real trading account names
    safety_checks_enabled: bool = True     # Whether safety checks are active
    max_position_size: float = 0.1        # Maximum position size as % of portfolio
    emergency_stop_enabled: bool = True    # Whether emergency stop is active
    
    # Portfolio Collection Settings
    portfolio_collection_enabled: bool = True  # Whether automatic portfolio collection is active
    collection_frequency_minutes: int = 15     # Scheduled collection frequency in minutes
    change_threshold_percent: float = 2.0      # Portfolio value change threshold for event-driven collection
    max_collections_per_hour: int = 60         # Maximum portfolio snapshots per hour
    data_retention_days: int = 30             # Days to keep detailed portfolio history
    enable_compression: bool = True            # Whether to compress historical data
    
    # Risk Management Settings
    max_portfolio_risk: float = 0.05          # 5% max portfolio risk exposure
    max_drawdown: float = 0.10                # 10% max portfolio drawdown
    daily_loss_limit: float = 1000.0          # $1000 daily loss limit
    weekly_loss_limit: float = 5000.0         # $5000 weekly loss limit
    monthly_loss_limit: float = 20000.0       # $20000 monthly loss limit
    max_single_position_size: float = 0.20    # 20% max single position size
    max_sector_exposure: float = 0.30         # 30% max sector exposure
    correlation_limit: float = 0.70           # 70% max correlation between positions
    leverage_limit: float = 1.0               # 1x max leverage
    default_stop_loss: float = 0.05           # 5% default stop loss
    default_take_profit: float = 0.15         # 15% default take profit
    trailing_stop_enabled: bool = True        # Enable trailing stops by default
    trailing_stop_distance: float = 0.03      # 3% trailing stop distance

@dataclass
class SignalRule:
    """Signal rule configuration."""
    rule_name: str
    rule_type: str
    threshold: Optional[float]
    signal_type: SignalType
    priority: SignalPriority
    enabled: bool
    confidence_formula: str
    reasoning_template: str

@dataclass
class ValidationRule:
    """Validation rule configuration."""
    rule_name: str
    rule_type: str
    enabled: bool
    min_confidence: Optional[float]
    max_frequency: Optional[int]
    cooldown_period: Optional[int]
    risk_threshold: Optional[float]
    volume_threshold: Optional[float]

@dataclass
class RoutingRule:
    """Routing rule configuration."""
    rule_name: str
    priority: SignalPriority
    handlers: List[str]
    timeout: float
    enabled: bool

class ConfigManager:
    """Manages dynamic configuration from database."""
    
    def __init__(self):
        self.db_client = None
        self._signal_rules: Dict[str, SignalRule] = {}
        self._validation_rules: Dict[str, ValidationRule] = {}
        self._routing_rules: Dict[str, RoutingRule] = {}
        self._risk_config: Dict[str, Any] = {}
        self._market_config: Dict[str, Any] = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache TTL
        
    async def initialize(self):
        """Initialize the configuration manager."""
        try:
            self.db_client = get_db_client()
            await self.load_all_config()
            logger.info("Configuration manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize configuration manager: {e}")
            raise
    
    async def load_all_config(self):
        """Load all configuration from database."""
        try:
            await asyncio.gather(
                self.load_signal_rules(),
                self.load_validation_rules(),
                self.load_routing_rules(),
                self.load_risk_config(),
                self.load_market_config()
            )
            self._cache_timestamp = datetime.utcnow()
            logger.info("All configuration loaded from database")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    async def load_signal_rules(self):
        """Load signal rules from database."""
        try:
            from common.db import execute_query
            
            query = """
                SELECT rule_name, rule_type, threshold, signal_type, priority, 
                       enabled, confidence_formula, reasoning_template
                FROM signal_rules 
                WHERE enabled = TRUE
                ORDER BY priority, rule_name
            """
            result = execute_query(query)
            
            self._signal_rules.clear()
            for row in result:
                rule = SignalRule(
                    rule_name=row['rule_name'],
                    rule_type=row['rule_type'],
                    threshold=row['threshold'],
                    signal_type=SignalType(row['signal_type']),
                    priority=SignalPriority(row['priority']),
                    enabled=row['enabled'],
                    confidence_formula=row['confidence_formula'],
                    reasoning_template=row['reasoning_template']
                )
                self._signal_rules[rule.rule_name] = rule
            
            logger.info(f"Loaded {len(self._signal_rules)} signal rules")
        except Exception as e:
            logger.error(f"Failed to load signal rules: {e}")
            raise
    
    async def load_validation_rules(self):
        """Load validation rules from database."""
        try:
            from common.db import execute_query
            
            query = """
                SELECT rule_name, rule_type, rule_definition, priority, enabled
                FROM validation_rules 
                WHERE enabled = TRUE
                ORDER BY priority, rule_name
            """
            result = execute_query(query)
            
            self._validation_rules.clear()
            for row in result:
                # Create a simple object with the required attributes
                rule = type('ValidationRule', (), {
                    'rule_name': row['rule_name'],
                    'rule_type': row['rule_type'],
                    'enabled': row['enabled'],
                    'rule_definition': row['rule_definition']
                })()
                self._validation_rules[rule.rule_name] = rule
            
            logger.info(f"Loaded {len(self._validation_rules)} validation rules")
        except Exception as e:
            logger.error(f"Failed to load validation rules: {e}")
            raise
    
    async def load_routing_rules(self):
        """Load routing rules from database."""
        try:
            from common.db import execute_query
            
            query = """
                SELECT rule_name, priority, handlers, timeout, enabled
                FROM routing_rules 
                WHERE enabled = TRUE
                ORDER BY priority, rule_name
            """
            result = execute_query(query)
            
            self._routing_rules.clear()
            for row in result:
                rule = RoutingRule(
                    rule_name=row['rule_name'],
                    priority=SignalPriority(row['priority']),
                    handlers=row['handlers'].split(',') if row['handlers'] else [],
                    timeout=float(row['timeout']) if row['timeout'] else 30.0,
                    enabled=row['enabled']
                )
                self._routing_rules[rule.rule_name] = rule
            
            logger.info(f"Loaded {len(self._routing_rules)} routing rules")
        except Exception as e:
            logger.error(f"Failed to load routing rules: {e}")
            raise
    
    async def load_risk_config(self):
        """Load risk configuration from database."""
        try:
            from common.db import execute_query
            
            query = """
                SELECT config_key, config_value, description
                FROM risk_config 
                WHERE enabled = TRUE
                ORDER BY config_key
            """
            result = execute_query(query)
            
            self._risk_config.clear()
            for row in result:
                self._risk_config[row['config_key']] = {
                    'value': row['config_value'],
                    'description': row['description']
                }
            
            logger.info(f"Loaded {len(self._risk_config)} risk config items")
        except Exception as e:
            logger.error(f"Failed to load risk config: {e}")
            raise
    
    async def load_market_config(self):
        """Load market configuration from database."""
        try:
            from common.db import execute_query
            
            query = """
                SELECT config_key, config_value, description
                FROM market_config 
                WHERE enabled = TRUE
                ORDER BY config_key
            """
            result = execute_query(query)
            
            self._market_config.clear()
            for row in result:
                self._market_config[row['config_key']] = {
                    'value': row['config_value'],
                    'description': row['description']
                }
            
            logger.info(f"Loaded {len(self._market_config)} market config items")
        except Exception as e:
            logger.error(f"Failed to load market config: {e}")
            raise
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache_timestamp is None:
            return False
        return (datetime.utcnow() - self._cache_timestamp).total_seconds() < self._cache_ttl
    
    async def refresh_if_needed(self):
        """Refresh configuration if cache is expired."""
        if not self._is_cache_valid():
            await self.load_all_config()
    
    # Signal Rules Methods
    async def get_signal_rules(self) -> Dict[str, SignalRule]:
        """Get all signal rules."""
        await self.refresh_if_needed()
        return self._signal_rules.copy()
    
    async def get_signal_rules_by_type(self, rule_type: str) -> List[SignalRule]:
        """Get signal rules by type."""
        await self.refresh_if_needed()
        return [rule for rule in self._signal_rules.values() if rule.rule_type == rule_type]
    
    async def get_signal_rule(self, rule_name: str) -> Optional[SignalRule]:
        """Get a specific signal rule."""
        await self.refresh_if_needed()
        return self._signal_rules.get(rule_name)
    
    # Validation Rules Methods
    async def get_validation_rules(self) -> Dict[str, ValidationRule]:
        """Get all validation rules."""
        await self.refresh_if_needed()
        return self._validation_rules.copy()
    
    async def get_validation_rule(self, rule_name: str) -> Optional[ValidationRule]:
        """Get a specific validation rule."""
        await self.refresh_if_needed()
        return self._validation_rules.get(rule_name)
    
    # Routing Rules Methods
    async def get_routing_rules(self) -> Dict[str, RoutingRule]:
        """Get all routing rules."""
        await self.refresh_if_needed()
        return self._routing_rules.copy()
    
    async def get_routing_rule_by_priority(self, priority: SignalPriority) -> Optional[RoutingRule]:
        """Get routing rule by priority."""
        await self.refresh_if_needed()
        for rule in self._routing_rules.values():
            if rule.priority == priority:
                return rule
        return None
    
    # Risk Config Methods
    async def get_risk_config(self) -> Dict[str, Any]:
        """Get all risk configuration."""
        await self.refresh_if_needed()
        return self._risk_config.copy()
    
    async def get_risk_config_value(self, key: str) -> Optional[Any]:
        """Get a specific risk configuration value."""
        await self.refresh_if_needed()
        config = self._risk_config.get(key)
        return config['value'] if config else None
    
    async def get_risk_config_by_category(self, category: str) -> Dict[str, Any]:
        """Get risk configuration by category."""
        await self.refresh_if_needed()
        return {k: v for k, v in self._risk_config.items() if v['category'] == category}
    
    # Market Config Methods
    async def get_market_config(self) -> Dict[str, Any]:
        """Get all market configuration."""
        await self.refresh_if_needed()
        return self._market_config.copy()
    
    async def get_market_config_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market configuration for a specific symbol."""
        await self.refresh_if_needed()
        return self._market_config.get(symbol)
    
    async def get_system_config(self) -> Dict[str, str]:
        """Get system configuration from database."""
        try:
            if not self.db_client:
                return {}
            
            query = "SELECT key, value FROM system_config"
            with self.db_client.get_session() as session:
                result = session.execute(query)
                config = {}
                for row in result:
                    config[row[0]] = row[1]
                return config
        except Exception as e:
            logger.error(f"Failed to get system config: {e}")
            return {}
    
    # Configuration Update Methods
    async def update_signal_rule(self, rule_name: str, updates: Dict[str, Any]):
        """Update a signal rule in the database."""
        try:
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key in ['threshold', 'signal_type', 'priority', 'enabled', 'confidence_formula', 'reasoning_template']:
                    set_clauses.append(f"{key} = ${len(values) + 2}")
                    values.append(value)
            
            if not set_clauses:
                return
            
            query = f"""
                UPDATE signal_rules 
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE rule_name = ${len(values) + 1}
            """
            values.append(rule_name)
            
            await self.db_client.execute(query, *values)
            await self.load_signal_rules()  # Refresh cache
            logger.info(f"Updated signal rule: {rule_name}")
        except Exception as e:
            logger.error(f"Failed to update signal rule {rule_name}: {e}")
            raise
    
    async def update_validation_rule(self, rule_name: str, updates: Dict[str, Any]):
        """Update a validation rule in the database."""
        try:
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key in ['enabled', 'min_confidence', 'max_frequency', 'cooldown_period', 'risk_threshold', 'volume_threshold']:
                    set_clauses.append(f"{key} = ${len(values) + 2}")
                    values.append(value)
            
            if not set_clauses:
                return
            
            query = f"""
                UPDATE validation_rules 
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE rule_name = ${len(values) + 1}
            """
            values.append(rule_name)
            
            await self.db_client.execute(query, *values)
            await self.load_validation_rules()  # Refresh cache
            logger.info(f"Updated validation rule: {rule_name}")
        except Exception as e:
            logger.error(f"Failed to update validation rule {rule_name}: {e}")
            raise
    
    async def update_risk_config(self, key: str, value: Any, description: str = None):
        """Update risk configuration in the database."""
        try:
            query = """
                UPDATE risk_config 
                SET config_value = $1, description = COALESCE($2, description), updated_at = CURRENT_TIMESTAMP
                WHERE config_key = $3
            """
            await self.db_client.execute(query, json.dumps(value), description, key)
            await self.load_risk_config()  # Refresh cache
            logger.info(f"Updated risk config: {key}")
        except Exception as e:
            logger.error(f"Failed to update risk config {key}: {e}")
            raise
    
    async def update_market_config(self, symbol: str, updates: Dict[str, Any]):
        """Update market configuration for a specific symbol."""
        try:
            from common.db import execute_query
            
            for key, value in updates.items():
                # Convert value to string for storage
                if isinstance(value, (list, dict)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                # Update or insert configuration
                upsert_query = """
                    INSERT INTO market_config (config_key, config_value, description, enabled, updated_at)
                    VALUES (%s, %s, %s, TRUE, NOW())
                    ON CONFLICT (config_key) 
                    DO UPDATE SET 
                        config_value = EXCLUDED.config_value,
                        updated_at = NOW()
                """
                
                config_key = f"{symbol}_{key}"
                execute_query(upsert_query, {
                    'config_key': config_key,
                    'config_value': value_str,
                    'description': f'Market config for {symbol} - {key}'
                })
            
            logger.info(f"Updated market config: {symbol}")
        except Exception as e:
            logger.error(f"Failed to update market config {symbol}: {e}")
            raise

    # Trading Configuration Methods
    async def load_trading_config(self) -> TradingConfig:
        """Load trading configuration from database or return defaults."""
        try:
            from common.db import execute_query
            
            query = """
                SELECT config_key, config_value, description
                FROM trading_config
                WHERE enabled = TRUE
                ORDER BY config_key
            """
            result = execute_query(query)
            
            # Default configuration
            config = TradingConfig(
                mode=TradingMode.SIMULATION,  # Safe default
                simulation_balance=10000.0,
                max_simulation_risk=0.02,
                real_trading_enabled=False,
                simulation_accounts=["simulation_main", "simulation_test"],
                real_accounts=["binance_us_main"],
                safety_checks_enabled=True,
                max_position_size=0.1,
                emergency_stop_enabled=True,
                # Portfolio Collection Settings
                portfolio_collection_enabled=True,
                collection_frequency_minutes=15,
                change_threshold_percent=2.0,
                max_collections_per_hour=60,
                data_retention_days=30,
                enable_compression=True,
                # Risk Management Settings
                max_portfolio_risk=0.05,
                max_drawdown=0.10,
                daily_loss_limit=1000.0,
                weekly_loss_limit=5000.0,
                monthly_loss_limit=20000.0,
                max_single_position_size=0.20,
                max_sector_exposure=0.30,
                correlation_limit=0.70,
                leverage_limit=1.0,
                default_stop_loss=0.05,
                default_take_profit=0.15,
                trailing_stop_enabled=True,
                trailing_stop_distance=0.03
            )
            
            # Override with database values
            for row in result:
                key = row['config_key']
                value = row['config_value']
                
                if key == 'trading_mode':
                    try:
                        config.mode = TradingMode(value.strip('"'))
                    except ValueError:
                        logger.warning(f"Invalid trading mode: {value}")
                elif key == 'simulation_balance':
                    config.simulation_balance = float(value)
                elif key == 'max_simulation_risk':
                    config.max_simulation_risk = float(value)
                elif key == 'real_trading_enabled':
                    config.real_trading_enabled = value.lower() == 'true'
                elif key == 'simulation_accounts':
                    config.simulation_accounts = json.loads(value)
                elif key == 'real_accounts':
                    config.real_accounts = json.loads(value)
                elif key == 'safety_checks_enabled':
                    config.safety_checks_enabled = value.lower() == 'true'
                elif key == 'max_position_size':
                    config.max_position_size = float(value)
                elif key == 'emergency_stop_enabled':
                    config.emergency_stop_enabled = value.lower() == 'true'
                # Portfolio Collection Settings
                elif key == 'portfolio_collection_enabled':
                    config.portfolio_collection_enabled = value.lower() == 'true'
                elif key == 'collection_frequency_minutes':
                    config.collection_frequency_minutes = int(value)
                elif key == 'change_threshold_percent':
                    config.change_threshold_percent = float(value)
                elif key == 'max_collections_per_hour':
                    config.max_collections_per_hour = int(value)
                elif key == 'data_retention_days':
                    config.data_retention_days = int(value)
                elif key == 'enable_compression':
                    config.enable_compression = value.lower() == 'true'
                # Risk Management Settings
                elif key == 'max_portfolio_risk':
                    config.max_portfolio_risk = float(value)
                elif key == 'max_drawdown':
                    config.max_drawdown = float(value)
                elif key == 'daily_loss_limit':
                    config.daily_loss_limit = float(value)
                elif key == 'weekly_loss_limit':
                    config.weekly_loss_limit = float(value)
                elif key == 'monthly_loss_limit':
                    config.monthly_loss_limit = float(value)
                elif key == 'max_single_position_size':
                    config.max_single_position_size = float(value)
                elif key == 'max_sector_exposure':
                    config.max_sector_exposure = float(value)
                elif key == 'correlation_limit':
                    config.correlation_limit = float(value)
                elif key == 'leverage_limit':
                    config.leverage_limit = float(value)
                elif key == 'default_stop_loss':
                    config.default_stop_loss = float(value)
                elif key == 'default_take_profit':
                    config.default_take_profit = float(value)
                elif key == 'trailing_stop_enabled':
                    config.trailing_stop_enabled = value.lower() == 'true'
                elif key == 'trailing_stop_distance':
                    config.trailing_stop_distance = float(value)
            
            return config
            
        except Exception as e:
            logger.warning(f"Failed to load trading config from database, using defaults: {e}")
            # Return default configuration
            return TradingConfig(
                mode=TradingMode.SIMULATION,
                simulation_balance=10000.0,
                max_simulation_risk=0.02,
                real_trading_enabled=False,
                simulation_accounts=["simulation_main", "simulation_test"],
                real_accounts=["binance_us_main"],
                safety_checks_enabled=True,
                max_position_size=0.1,
                emergency_stop_enabled=True,
                # Portfolio Collection Settings
                portfolio_collection_enabled=True,
                collection_frequency_minutes=15,
                change_threshold_percent=2.0,
                max_collections_per_hour=60,
                data_retention_days=30,
                enable_compression=True,
                # Risk Management Settings
                max_portfolio_risk=0.05,
                max_drawdown=0.10,
                daily_loss_limit=1000.0,
                weekly_loss_limit=5000.0,
                monthly_loss_limit=20000.0,
                max_single_position_size=0.20,
                max_sector_exposure=0.30,
                correlation_limit=0.70,
                leverage_limit=1.0,
                default_stop_loss=0.05,
                default_take_profit=0.15,
                trailing_stop_enabled=True,
                trailing_stop_distance=0.03
            )
    
    async def update_trading_config(self, updates: Dict[str, Any]) -> bool:
        """Update trading configuration in database."""
        try:
            from common.db import execute_query
            
            for key, value in updates.items():
                # Convert value to string for storage
                if isinstance(value, (list, dict)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                # Update or insert configuration using named parameters
                upsert_query = """
                    INSERT INTO trading_config (config_key, config_value, description, enabled, updated_at)
                    VALUES (:config_key, :config_value, :description, TRUE, NOW())
                    ON CONFLICT (config_key) 
                    DO UPDATE SET 
                        config_value = EXCLUDED.config_value,
                        updated_at = NOW()
                """
                
                # Pass parameters as a dictionary with named keys
                from common.db import execute_non_query
                execute_non_query(upsert_query, {
                    'config_key': key,
                    'config_value': value_str,
                    'description': f'Updated via API at {datetime.now().isoformat()}'
                })
            
            logger.info(f"Updated trading config: {list(updates.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update trading config: {e}")
            return False
    
    async def is_simulation_mode(self) -> bool:
        """Check if system is currently in simulation mode."""
        try:
            config = await self.load_trading_config()
            return config.mode == TradingMode.SIMULATION
        except Exception as e:
            logger.warning(f"Failed to check simulation mode, defaulting to True: {e}")
            return True  # Safe default
    
    async def get_trading_mode(self) -> TradingMode:
        """Get current trading mode."""
        try:
            config = await self.load_trading_config()
            return config.mode
        except Exception as e:
            logger.warning(f"Failed to get trading mode, defaulting to SIMULATION: {e}")
            return TradingMode.SIMULATION  # Safe default
    
    async def is_real_trading_enabled(self) -> bool:
        """Check if real trading is enabled."""
        config = await self.load_trading_config()
        return config.real_trading_enabled and config.mode == TradingMode.REAL_TRADING
    
    async def is_hybrid_mode(self) -> bool:
        """Check if system is in hybrid mode (both simulation and real)."""
        config = await self.load_trading_config()
        return config.mode == TradingMode.HYBRID
    
    async def get_simulation_balance(self) -> float:
        """Get simulation account balance."""
        config = await self.load_trading_config()
        return config.simulation_balance
    
    async def get_max_position_size(self) -> float:
        """Get maximum position size as percentage of portfolio."""
        config = await self.load_trading_config()
        return config.max_position_size
    
    async def get_portfolio_collection_config(self) -> Dict[str, Any]:
        """Get portfolio collection configuration."""
        try:
            config = await self.load_trading_config()
            return {
                'enabled': config.portfolio_collection_enabled,
                'frequency_minutes': config.collection_frequency_minutes,
                'change_threshold_percent': config.change_threshold_percent,
                'max_collections_per_hour': config.max_collections_per_hour,
                'data_retention_days': config.data_retention_days,
                'enable_compression': config.enable_compression
            }
        except Exception as e:
            logger.warning(f"Failed to get portfolio collection config, using defaults: {e}")
            return {
                'enabled': True,
                'frequency_minutes': 15,
                'change_threshold_percent': 2.0,
                'max_collections_per_hour': 60,
                'data_retention_days': 30,
                'enable_compression': True
            }
    
    async def update_portfolio_collection_config(self, updates: Dict[str, Any]) -> bool:
        """Update portfolio collection configuration."""
        try:
            # Validate updates
            if 'frequency_minutes' in updates:
                if not 1 <= updates['frequency_minutes'] <= 1440:  # 1 min to 24 hours
                    raise ValueError("Collection frequency must be between 1 and 1440 minutes")
            
            if 'change_threshold_percent' in updates:
                if not 0.1 <= updates['change_threshold_percent'] <= 50.0:
                    raise ValueError("Change threshold must be between 0.1% and 50%")
            
            if 'max_collections_per_hour' in updates:
                if not 1 <= updates['max_collections_per_hour'] <= 3600:
                    raise ValueError("Max collections per hour must be between 1 and 3600")
            
            # Update the configuration
            return await self.update_trading_config(updates)
            
        except Exception as e:
            logger.error(f"Failed to update portfolio collection config: {e}")
            return False
    
    async def should_collect_portfolio_snapshot(self, current_value: float, last_value: float = None) -> bool:
        """Determine if portfolio snapshot should be collected based on smart logic."""
        try:
            config = await self.get_portfolio_collection_config()
            
            if not config['enabled']:
                return False
            
            # Check if change threshold is met
            if last_value and last_value > 0:
                change_percent = abs((current_value - last_value) / last_value) * 100
                if change_percent >= config['change_threshold_percent']:
                    logger.info(f"Portfolio change threshold met: {change_percent:.2f}% >= {config['change_threshold_percent']}%")
                    return True
            
            # Check if scheduled collection time has passed
            # Since we don't have a persistent scheduler, collect every time for now
            # This ensures we get regular updates for the UI
            logger.info(f"Portfolio collection scheduled - collecting snapshot")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to check portfolio collection logic, defaulting to True: {e}")
            return True  # Safe default
            
        except Exception as e:
            logger.warning(f"Failed to check portfolio collection logic, defaulting to True: {e}")
            return True  # Safe default

# Global configuration manager instance
config_manager = ConfigManager()
