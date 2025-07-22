# VolexSwarm Database Schema

This document describes the database schema for VolexSwarm and any recent changes.

## Overview

VolexSwarm uses PostgreSQL with TimescaleDB extension for time-series data. The database is designed to handle:
- Trading strategies and their parameters
- Market data (price data, signals, trades)
- Agent logs and system configuration
- Backtest results and performance metrics

## Schema Setup

### For New Deployments

Use the automated schema setup script:

```bash
python scripts/database/setup_schema.py
```

This script will:
1. Create the TimescaleDB extension
2. Create all tables using SQLAlchemy models
3. Check for and fix any schema inconsistencies
4. Create performance indexes

### For Existing Deployments

If you have an existing database that needs schema updates, the setup script will automatically detect and fix missing columns.

## Recent Schema Changes

### Added `agent_name` Column to `strategies` Table

**Date**: July 22, 2025  
**Reason**: Strategy agent requires this column to identify which agent created the strategy.

```sql
ALTER TABLE strategies ADD COLUMN agent_name VARCHAR(50) NOT NULL DEFAULT 'strategy';
```

### Added `executed_at` Column to `trades` Table

**Date**: July 22, 2025  
**Reason**: Required for proper time-series indexing and trade tracking.

```sql
ALTER TABLE trades ADD COLUMN executed_at TIMESTAMP WITH TIME ZONE;
```

### Added `log_context` Column to `agent_logs` Table

**Date**: July 22, 2025  
**Reason**: Allows agents to store additional context data with log entries.

```sql
ALTER TABLE agent_logs ADD COLUMN log_context JSONB;
```

## Table Structure

### Core Tables

#### `strategies`
- `id` (Primary Key)
- `name` (Unique)
- `description`
- `agent_name` (NEW) - Which agent created the strategy
- `parameters` (JSONB) - Strategy parameters and configuration
- `is_active` - Whether the strategy is currently active
- `created_at`, `updated_at`

#### `trades`
- `executed_at` (Primary Key, NEW) - When the trade was executed
- `trade_id` (Unique)
- `strategy_id` (Foreign Key)
- `symbol`, `exchange`
- `side` (buy/sell)
- `quantity`, `price`
- `status`, `fees`
- `trade_metadata` (JSONB)

#### `agent_logs`
- `timestamp` (Primary Key)
- `agent_name`
- `level` (DEBUG, INFO, WARNING, ERROR)
- `message`
- `log_context` (JSONB, NEW) - Additional context data
- `traceback`

### Time-Series Tables

#### `price_data`
- `time` (Primary Key)
- `symbol`, `exchange`
- `open`, `high`, `low`, `close`, `volume`
- `timeframe`

#### `signals`
- `timestamp` (Primary Key)
- `strategy_id` (Foreign Key)
- `symbol`, `signal_type`, `strength`, `confidence`
- `timeframe`, `indicators` (JSONB)

### Supporting Tables

#### `orders`
- Order lifecycle tracking
- Links to strategies and trades

#### `backtests`
- Backtest results and configurations
- Performance metrics storage

#### `performance_metrics`
- Historical performance data
- Analytics and reporting

#### `system_config`
- System-wide configuration
- Agent settings

#### `portfolios`
- Current positions and balances
- Real-time portfolio tracking

#### `market_data`
- Additional market data beyond price
- Sentiment, news, volume profiles

## Indexes

The following indexes are created for performance:

```sql
-- Price data indexes
CREATE INDEX idx_price_data_time_symbol ON price_data (time, symbol);
CREATE INDEX idx_price_data_exchange_symbol_time ON price_data (exchange, symbol, time);

-- Trade indexes
CREATE INDEX idx_trades_executed_at_symbol ON trades (executed_at, symbol);
CREATE INDEX idx_orders_symbol_created ON orders (symbol, created_at);
CREATE INDEX idx_orders_strategy_created ON orders (strategy_id, created_at);

-- Signal indexes
CREATE INDEX idx_signals_timestamp_symbol ON signals (timestamp, symbol);

-- Strategy indexes
CREATE INDEX idx_strategies_name ON strategies (name);
CREATE INDEX idx_strategies_agent_name ON strategies (agent_name);

-- Log indexes
CREATE INDEX idx_agent_logs_timestamp_agent ON agent_logs (timestamp, agent_name);

-- Backtest indexes
CREATE INDEX idx_backtests_strategy_created ON backtests (strategy_id, created_at);
```

## Migration Notes

### For Developers

When making schema changes:

1. **Update the SQLAlchemy models** in `common/models.py`
2. **Update the setup script** in `scripts/database/setup_schema.py`
3. **Document the changes** in this file
4. **Test the migration** on a fresh database

### For Production Deployments

1. **Backup the database** before making schema changes
2. **Run the setup script** to apply changes
3. **Verify the changes** work with all agents
4. **Monitor for any issues** after deployment

## Troubleshooting

### Common Issues

1. **Missing columns**: Run `python scripts/database/setup_schema.py`
2. **Index creation failures**: Check if tables exist first
3. **Connection issues**: Verify database container is running
4. **Permission errors**: Check database user permissions

### Reset Database

To completely reset the database:

```bash
python scripts/database/reset.py
python scripts/database/setup_schema.py
```

This will drop and recreate the database with the correct schema. 