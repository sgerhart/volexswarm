# VolexSwarm Database

## 🗄️ **Database Overview**

VolexSwarm uses **TimescaleDB** (PostgreSQL extension) as its primary database, optimized for time-series data and high-performance trading operations. The database is designed to handle large volumes of market data, trading signals, and system metrics with efficient querying capabilities.

## 🏗️ **Database Architecture**

### **Technology Stack**
- **Primary Database**: TimescaleDB 14 (PostgreSQL extension)
- **Container**: `timescale/timescaledb:latest-pg14`
- **Port**: 5432
- **Credentials**: `volex:volex_pass`
- **Database Name**: `volextrades`

### **Key Features**
- **Time-Series Optimization**: Automatic partitioning by time
- **Hypertables**: Efficient storage for time-series data
- **Continuous Aggregates**: Pre-computed aggregations for fast queries
- **Compression**: Automatic data compression for historical data
- **Retention Policies**: Automated data lifecycle management

## 📊 **Core Tables**

### **1. Market Data Tables**

#### **price_data**
```sql
CREATE TABLE price_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(20,8),
    high DECIMAL(20,8),
    low DECIMAL(20,8),
    close DECIMAL(20,8),
    volume DECIMAL(20,8),
    timeframe VARCHAR(10) NOT NULL
);

-- Convert to hypertable
SELECT create_hypertable('price_data', 'timestamp');
```

#### **market_data**
```sql
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    source VARCHAR(50),
    quality_score DECIMAL(3,2)
);
```

### **2. Trading Tables**

#### **trades**
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'buy' or 'sell'
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    strategy_id VARCHAR(50),
    agent_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    exchange_order_id VARCHAR(100),
    fees DECIMAL(20,8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **signals**
```sql
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- 'buy', 'sell', 'hold'
    strength DECIMAL(3,2) NOT NULL, -- 0.0 to 1.0
    timestamp TIMESTAMPTZ NOT NULL,
    strategy_id VARCHAR(50),
    agent_id VARCHAR(50),
    confidence DECIMAL(3,2),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **orders**
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL, -- 'market', 'limit', 'stop'
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8),
    status VARCHAR(20) DEFAULT 'pending',
    timestamp TIMESTAMPTZ NOT NULL,
    strategy_id VARCHAR(50),
    agent_id VARCHAR(50),
    exchange_order_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **3. Strategy Tables**

#### **strategies**
```sql
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **strategy_performance**
```sql
CREATE TABLE strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    symbol VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_return DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    win_rate DECIMAL(5,2),
    total_trades INTEGER,
    profitable_trades INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **sandbox_results**
```sql
CREATE TABLE sandbox_results (
    id SERIAL PRIMARY KEY,
    sandbox_id VARCHAR(100) UNIQUE NOT NULL,
    strategy_data JSONB NOT NULL,
    backtest_results JSONB NOT NULL,
    performance_metrics JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### **4. News and Sentiment Tables**

#### **news_articles**
```sql
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source VARCHAR(100),
    url TEXT,
    published_at TIMESTAMPTZ,
    symbols TEXT[], -- Array of affected symbols
    relevance_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **sentiment_analysis**
```sql
CREATE TABLE sentiment_analysis (
    id SERIAL PRIMARY KEY,
    news_article_id INTEGER REFERENCES news_articles(id),
    symbol VARCHAR(20) NOT NULL,
    sentiment_score DECIMAL(3,2) NOT NULL, -- -1.0 to 1.0
    confidence DECIMAL(3,2),
    analysis_timestamp TIMESTAMPTZ NOT NULL,
    agent_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **5. System Tables**

#### **agent_status**
```sql
CREATE TABLE agent_status (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'online', 'offline', 'error'
    health_score DECIMAL(3,2),
    last_heartbeat TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **system_events**
```sql
CREATE TABLE system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'error', 'critical'
    message TEXT NOT NULL,
    agent_id VARCHAR(50),
    metadata JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

## 🔧 **Database Management**

### **Connection Details**
```bash
# Direct connection
psql -h localhost -p 5432 -U volex -d volextrades

# Docker connection
docker exec -it volexstorm-db psql -U volex -d volextrades
```

### **Environment Variables**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=volextrades
DB_USER=volex
DB_PASSWORD=volex_pass
```

### **Health Check**
```sql
-- Check database health
SELECT version();
SELECT current_database();
SELECT current_user;

-- Check TimescaleDB extension
SELECT * FROM pg_extension WHERE extname = 'timescaledb';
```

## 📈 **Performance Optimization**

### **Indexes**
```sql
-- Time-based indexes for hypertables
CREATE INDEX idx_price_data_symbol_time ON price_data (symbol, timestamp DESC);
CREATE INDEX idx_trades_symbol_time ON trades (symbol, timestamp DESC);
CREATE INDEX idx_signals_symbol_time ON signals (symbol, timestamp DESC);

-- Symbol-based indexes
CREATE INDEX idx_price_data_symbol ON price_data (symbol);
CREATE INDEX idx_trades_symbol ON trades (symbol);
CREATE INDEX idx_signals_symbol ON signals (symbol);
```

### **Partitioning**
```sql
-- Enable compression on older data
ALTER TABLE price_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Set compression policy (compress data older than 7 days)
SELECT add_compression_policy('price_data', INTERVAL '7 days');
```

### **Retention Policies**
```sql
-- Keep price data for 1 year
SELECT add_retention_policy('price_data', INTERVAL '1 year');

-- Keep trades for 5 years
SELECT add_retention_policy('trades', INTERVAL '5 years');
```

## 🔍 **Common Queries**

### **Market Data Queries**
```sql
-- Get latest price for a symbol
SELECT * FROM price_data 
WHERE symbol = 'BTCUSDT' 
ORDER BY timestamp DESC 
LIMIT 1;

-- Get price history for a symbol
SELECT timestamp, close, volume 
FROM price_data 
WHERE symbol = 'BTCUSDT' 
  AND timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp;

-- Get OHLCV data for a specific timeframe
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume
FROM price_data 
WHERE symbol = 'BTCUSDT' 
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour;
```

### **Trading Queries**
```sql
-- Get recent trades
SELECT symbol, side, quantity, price, timestamp 
FROM trades 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Get trading performance by symbol
SELECT 
    symbol,
    COUNT(*) as total_trades,
    SUM(CASE WHEN side = 'buy' THEN quantity * price ELSE 0 END) as buy_volume,
    SUM(CASE WHEN side = 'sell' THEN quantity * price ELSE 0 END) as sell_volume
FROM trades 
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY symbol;
```

### **Strategy Performance Queries**
```sql
-- Get strategy performance summary
SELECT 
    s.name,
    sp.symbol,
    sp.total_return,
    sp.sharpe_ratio,
    sp.max_drawdown,
    sp.win_rate
FROM strategy_performance sp
JOIN strategies s ON sp.strategy_id = s.id
WHERE sp.end_date >= NOW() - INTERVAL '30 days'
ORDER BY sp.total_return DESC;
```

## 🛠️ **Maintenance Tasks**

### **Regular Maintenance**
```sql
-- Update table statistics
ANALYZE;

-- Vacuum tables
VACUUM ANALYZE price_data;
VACUUM ANALYZE trades;
VACUUM ANALYZE signals;

-- Check for long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

### **Backup and Recovery**
```bash
# Create database backup
pg_dump -h localhost -U volex -d volextrades > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql -h localhost -U volex -d volextrades < backup_file.sql
```

## 📊 **Monitoring and Metrics**

### **Database Size**
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### **Performance Metrics**
```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check connection count
SELECT count(*) FROM pg_stat_activity;
```

---

**Last Updated**: 2025-01-26  
**Version**: 7.1 (Consolidated Database Edition)
