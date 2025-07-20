# VolexSwarm Signal Agent Documentation

## 📋 **Overview**

The VolexSwarm Signal Agent is an advanced autonomous AI trading signal generator that combines technical analysis, machine learning, and GPT-enhanced reasoning to generate intelligent trading signals. It provides real-time market analysis, autonomous decision-making capabilities, and comprehensive signal generation with confidence scoring.

**Version**: 1.0.0  
**Port**: 8003 (Docker) / 8003 (Local)  
**Status**: ✅ Fully Implemented and Operational

---

## 🏗️ **Architecture**

### **Core Components**

The Signal Agent follows a sophisticated multi-layered architecture:

#### 1. **TechnicalIndicators Class**
- **Purpose**: Pure technical analysis calculations
- **Capabilities**:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Stochastic Oscillator
- **Features**: Stateless calculations with configurable parameters

#### 2. **AutonomousSignalAgent Class**
- **Purpose**: Main signal generation and decision-making engine
- **Capabilities**:
  - Machine learning model training and inference
  - Feature engineering and technical analysis
  - Autonomous decision making with confidence scoring
  - GPT-enhanced reasoning and market commentary
  - Signal history tracking and pattern analysis

#### 3. **AI Integration**
- **Machine Learning**: Random Forest Classifier for signal prediction
- **GPT Enhancement**: OpenAI integration for market commentary and decision validation
- **Feature Engineering**: Advanced feature extraction from price and volume data
- **Model Management**: Automatic model training and performance tracking

---

## 🔧 **Technical Implementation**

### **Dependencies**
```python
# Core Framework
fastapi
uvicorn
numpy
pandas

# Machine Learning
scikit-learn
joblib

# Technical Analysis
ta  # Technical analysis library

# AI/ML
openai
tiktoken

# Database
sqlalchemy
asyncpg
psycopg2-binary

# Security
hvac  # Vault integration

# Utilities
python-dotenv
```

### **Key Features**

#### **Technical Analysis**
- **RSI**: Overbought/oversold detection (30/70 thresholds)
- **MACD**: Trend following with signal line crossovers
- **Bollinger Bands**: Volatility and price position analysis
- **Stochastic**: Momentum oscillator with %K and %D lines
- **Custom Indicators**: Volume analysis and price momentum

#### **Machine Learning**
- **Random Forest Classifier**: Ensemble learning for signal prediction
- **Feature Engineering**: 10+ technical and price-based features
- **Model Training**: Automatic training on historical data
- **Confidence Scoring**: Probability-based decision confidence
- **Performance Tracking**: Model accuracy and signal quality metrics

#### **Autonomous Decision Making**
- **Signal Generation**: Buy/sell/hold signals with confidence scores
- **Risk Assessment**: Position sizing and risk level determination
- **Pattern Recognition**: Historical signal pattern analysis
- **Trend Analysis**: Market trend identification and strength measurement

#### **GPT Enhancement**
- **Market Commentary**: AI-generated market analysis
- **Decision Validation**: GPT review of autonomous decisions
- **Risk Analysis**: AI-powered risk assessment
- **Reasoning Enhancement**: Natural language explanation of decisions

---

## 🌐 **API Endpoints**

### **Health & Status**

#### `GET /health`
**Comprehensive health check**
```json
{
  "status": "healthy",
  "vault_connected": true,
  "database_connected": true,
  "agent_ready": true,
  "autonomous_mode": true,
  "models_loaded": 5,
  "agent": "signal"
}
```

### **Signal Generation**

#### `POST /signals/generate`
**Generate autonomous trading signal**
```json
// Request
{
  "symbol": "BTC/USDT",
  "strategy_id": 1
}

// Response
{
  "agent": "signal",
  "symbol": "BTC/USDT",
  "signal": {
    "signal_type": "buy",
    "confidence": 0.85,
    "strength": 0.75,
    "technical_signals": [
      ["RSI oversold", 0.8],
      ["MACD bullish crossover", 0.6]
    ],
    "ml_prediction": 1,
    "ml_confidence": 0.82,
    "indicators": {
      "rsi": 28.5,
      "macd": 0.0023,
      "bb_position": 0.15,
      "stochastic_k": 25.3,
      "stochastic_d": 30.1
    },
    "gpt_commentary": {
      "market_sentiment": "bullish",
      "key_factors": ["oversold conditions", "momentum shift"],
      "risk_assessment": "moderate"
    },
    "timestamp": "2025-07-20T17:45:30.123456",
    "price": 45000.0
  },
  "autonomous": true
}
```

#### `GET /signals`
**Get signal history**
```json
{
  "agent": "signal",
  "signals": [
    {
      "timestamp": "2025-07-20T17:45:30.123456",
      "symbol": "BTC/USDT",
      "signal_type": "buy",
      "strength": 0.75,
      "confidence": 0.85,
      "timeframe": "1h",
      "strategy_id": 1,
      "indicators": {...},
      "autonomous": true
    }
  ],
  "total": 50
}
```

### **Technical Indicators**

#### `GET /indicators/{symbol}`
**Get current technical indicators**
```json
{
  "agent": "signal",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "current_price": 45000.0,
  "indicators": {
    "rsi": 28.5,
    "macd": {
      "line": 0.0023,
      "signal": 0.0018,
      "histogram": 0.0005
    },
    "bollinger_bands": {
      "upper": 46500.0,
      "middle": 45000.0,
      "lower": 43500.0,
      "position": 0.15
    },
    "stochastic": {
      "k": 25.3,
      "d": 30.1
    }
  },
  "timestamp": "2025-07-20T17:45:30.123456"
}
```

### **Machine Learning**

#### `POST /models/train`
**Train ML model for a symbol**
```json
// Request
{
  "symbol": "BTC/USDT"
}

// Response
{
  "agent": "signal",
  "symbol": "BTC/USDT",
  "status": "success",
  "message": "Model trained successfully for BTC/USDT",
  "data_points": 2160
}
```

#### `GET /models/performance`
**Get model performance metrics**
```json
{
  "agent": "signal",
  "models": {
    "BTC/USDT": {
      "model_trained": true,
      "insights": {
        "trend": "bullish",
        "trend_strength": 0.65,
        "buy_signals_count": 15,
        "sell_signals_count": 8,
        "avg_buy_confidence": 0.78,
        "avg_sell_confidence": 0.72,
        "signal_volatility": 0.12,
        "recommendation": "Strong buy - Multiple indicators align for upward movement"
      },
      "signal_count": 45
    }
  },
  "total_models": 5,
  "autonomous_mode": true
}
```

### **Autonomous AI**

#### `GET /autonomous/insights/{symbol}`
**Get autonomous AI insights**
```json
{
  "agent": "signal",
  "symbol": "BTC/USDT",
  "insights": {
    "trend": "bullish",
    "trend_strength": 0.65,
    "buy_signals_count": 15,
    "sell_signals_count": 8,
    "avg_buy_confidence": 0.78,
    "avg_sell_confidence": 0.72,
    "signal_volatility": 0.12,
    "recommendation": "Strong buy - Multiple indicators align for upward movement",
    "last_updated": "2025-07-20T17:45:30.123456"
  },
  "autonomous": true
}
```

#### `POST /autonomous/decide`
**Make autonomous trading decision**
```json
// Request
{
  "symbol": "BTC/USDT",
  "current_balance": 10000.0
}

// Response
{
  "agent": "signal",
  "symbol": "BTC/USDT",
  "decision": {
    "action": "buy",
    "reason": "Strong buy signal with 85.0% confidence | GPT Analysis: Confirmed",
    "confidence": 0.935,
    "position_size": 1000.0,
    "risk_level": "low"
  },
  "signal": {
    "signal_type": "buy",
    "confidence": 0.85,
    "strength": 0.75,
    "technical_signals": [...],
    "ml_prediction": 1,
    "ml_confidence": 0.82,
    "indicators": {...},
    "gpt_commentary": {...}
  },
  "autonomous": true,
  "gpt_analysis": {
    "recommendation": "confirm",
    "reasoning": "Strong technical indicators support bullish momentum",
    "risk_assessment": "low",
    "market_context": "Oversold conditions with positive momentum shift"
  },
  "openai_available": true,
  "timestamp": "2025-07-20T17:45:30.123456"
}
```

---

## 📊 **Technical Indicators**

### **RSI (Relative Strength Index)**
- **Purpose**: Momentum oscillator measuring speed and magnitude of price changes
- **Calculation**: 14-period default, 30/70 overbought/oversold thresholds
- **Signals**: 
  - RSI < 30: Oversold (bullish signal)
  - RSI > 70: Overbought (bearish signal)
  - RSI 30-70: Neutral zone

### **MACD (Moving Average Convergence Divergence)**
- **Purpose**: Trend-following momentum indicator
- **Components**: MACD line, signal line, histogram
- **Signals**:
  - MACD line crosses above signal line: Bullish crossover
  - MACD line crosses below signal line: Bearish crossover
  - Histogram divergence: Trend strength indication

### **Bollinger Bands**
- **Purpose**: Volatility indicator with support/resistance levels
- **Components**: Upper band, middle band (SMA), lower band
- **Signals**:
  - Price touches lower band: Potential oversold
  - Price touches upper band: Potential overbought
  - Band width: Volatility measurement

### **Stochastic Oscillator**
- **Purpose**: Momentum indicator comparing closing price to price range
- **Components**: %K line, %D line (signal line)
- **Signals**:
  - %K < 20: Oversold conditions
  - %K > 80: Overbought conditions
  - %K crosses %D: Momentum shifts

---

## 🤖 **Machine Learning Features**

### **Feature Engineering**
```python
# Technical Features
rsi_value = rsi[-1]
macd_value = macd_line[-1]
bb_position = (price - bb_lower) / (bb_upper - bb_lower)
stoch_k = stochastic_k[-1]
stoch_d = stochastic_d[-1]

# Price Features
price_momentum = price[-1] / price[-5] - 1
price_volatility = std(price_changes[-20:])

# Volume Features
volume_ratio = current_volume / avg_volume
volume_volatility = std(volumes[-20:]) / avg_volume
```

### **Model Training**
- **Algorithm**: Random Forest Classifier
- **Training Data**: 90 days of historical price data
- **Labels**: Buy (1), Hold (0), Sell (-1) based on 2% return threshold
- **Features**: 10+ technical and price-based features
- **Validation**: Cross-validation and performance metrics

### **Signal Prediction**
- **Input**: Current market features
- **Output**: Signal type and confidence score
- **Threshold**: 70% confidence for autonomous decisions
- **Ensemble**: Multiple models for different timeframes

---

## 🧠 **Autonomous Decision Making**

### **Signal Generation Process**
1. **Data Collection**: Historical price and volume data
2. **Technical Analysis**: Calculate all technical indicators
3. **Feature Extraction**: Prepare features for ML model
4. **ML Prediction**: Get model prediction and confidence
5. **Signal Synthesis**: Combine technical and ML signals
6. **GPT Enhancement**: AI-powered market commentary
7. **Decision Output**: Final signal with confidence and reasoning

### **Decision Logic**
```python
# Signal strength calculation
signal_strength = 0.0

# Technical signals
if rsi < 30:
    signal_strength += 0.3
if macd_bullish_crossover:
    signal_strength += 0.2
if bb_oversold:
    signal_strength += 0.25

# ML signals
if ml_prediction == 1 and ml_confidence > 0.7:
    signal_strength += 0.4

# Final decision
if signal_strength > 0.5:
    signal_type = "buy"
elif signal_strength < -0.5:
    signal_type = "sell"
else:
    signal_type = "hold"
```

### **Risk Management**
- **Confidence Threshold**: 70% minimum for autonomous decisions
- **Position Sizing**: 10% of portfolio per trade
- **Risk Levels**: Low, medium, high based on confidence
- **Stop Loss**: 5% automatic stop loss
- **Max Risk**: 2% maximum risk per trade

---

## 🔐 **Security & Configuration**

### **Vault Integration**
- **API Keys**: OpenAI API key stored securely in Vault
- **Configuration**: Agent settings from Vault
- **Credentials**: Database and external service credentials

### **Environment Variables**
```bash
# Required
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=root

# Optional
OPENAI_API_KEY=your_openai_key  # For GPT enhancement
AUTONOMOUS_MODE=true  # Enable autonomous decision making
LOG_LEVEL=INFO
DEBUG=false
```

### **Configuration**
```bash
# Store signal agent configuration in Vault
docker exec -it volexswarm-vault vault kv put secret/agents/signal \
  autonomous_mode="true" \
  confidence_threshold="0.7" \
  max_positions="3" \
  position_sizing="0.1" \
  model_retrain_interval="7"
```

---

## 🚀 **Usage Examples**

### **Basic Signal Generation**
```bash
# Generate signal for BTC/USDT
curl -X POST http://localhost:8003/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT"}'

# Get technical indicators
curl http://localhost:8003/indicators/BTC/USDT

# Get autonomous insights
curl http://localhost:8003/autonomous/insights/BTC/USDT
```

### **Python Integration**
```python
import requests

# Initialize signal agent client
signal_url = "http://localhost:8003"

# Generate autonomous signal
signal_data = {
    "symbol": "BTC/USDT"
}
response = requests.post(f"{signal_url}/signals/generate", json=signal_data)
signal_result = response.json()

# Make autonomous decision
decision_data = {
    "symbol": "BTC/USDT",
    "current_balance": 10000.0
}
response = requests.post(f"{signal_url}/autonomous/decide", json=decision_data)
decision_result = response.json()

# Train ML model
response = requests.post(f"{signal_url}/models/train", json={"symbol": "BTC/USDT"})
training_result = response.json()
```

### **Integration with Other Agents**
```python
# Meta-Agent can request signals
signal = await signal_agent.generate_signal("BTC/USDT")

# Execution Agent can use autonomous decisions
decision = await signal_agent.autonomous_decision("BTC/USDT", balance=10000)
if decision['action'] == 'buy' and decision['confidence'] > 0.8:
    order = await execution_agent.place_order(decision_to_order(decision))

# Research Agent can provide market context
research_data = await research_agent.research_symbol("BTC/USDT")
enhanced_signal = await signal_agent.generate_signal_with_context("BTC/USDT", research_data)
```

---

## 📈 **Performance & Monitoring**

### **Performance Metrics**
- **Signal Accuracy**: > 60% win rate target
- **Response Time**: < 1 second for signal generation
- **Model Performance**: > 70% prediction accuracy
- **GPT Integration**: 99%+ availability

### **Monitoring**
- **Health Checks**: `/health` endpoint with component status
- **Model Performance**: Automatic accuracy tracking
- **Signal Quality**: Confidence and strength metrics
- **GPT Usage**: OpenAI API call monitoring

### **Database Integration**
- **Signal Storage**: All signals stored in TimescaleDB
- **Model Persistence**: Trained models saved for reuse
- **Performance Tracking**: Historical accuracy metrics
- **Audit Trail**: Complete signal generation history

---

## 🔧 **Deployment**

### **Docker Deployment**
```bash
# Build and run signal agent
docker-compose up signal

# Or run individually
docker build -f docker/signal.Dockerfile -t volexswarm-signal .
docker run -p 8003:8003 volexswarm-signal
```

### **Local Development**
```bash
# Activate virtual environment
pyenv activate volexswarm-env

# Set environment variables
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=root
export OPENAI_API_KEY=your_openai_key

# Run signal agent
cd agents/signal
python main.py
```

### **Production Configuration**
```bash
# Configure for production
docker exec -it volexswarm-vault vault kv put secret/agents/signal \
  autonomous_mode="true" \
  confidence_threshold="0.75" \
  max_positions="5" \
  position_sizing="0.08" \
  model_retrain_interval="3"
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Model Training Failed**
```bash
# Check data availability
curl http://localhost:8003/indicators/BTC/USDT

# Retrain model manually
curl -X POST http://localhost:8003/models/train \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT"}'
```

#### **GPT Integration Issues**
```bash
# Check OpenAI configuration
docker exec -it volexswarm-vault vault kv get secret/openai

# Test GPT availability
curl http://localhost:8003/autonomous/insights/BTC/USDT
```

#### **Signal Generation Errors**
```bash
# Check agent health
curl http://localhost:8003/health

# Verify data availability
curl http://localhost:8003/indicators/BTC/USDT
```

### **Debug Commands**
```bash
# Check agent logs
docker logs volexswarm-signal-1

# Test signal generation
curl -X POST http://localhost:8003/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT"}'

# Check model performance
curl http://localhost:8003/models/performance
```

---

## 📚 **API Reference**

### **Request/Response Formats**

#### **Signal Generation Request**
```json
{
  "symbol": "BTC/USDT",
  "strategy_id": 1
}
```

#### **Signal Response**
```json
{
  "signal_type": "buy",
  "confidence": 0.85,
  "strength": 0.75,
  "technical_signals": [
    ["RSI oversold", 0.8],
    ["MACD bullish crossover", 0.6]
  ],
  "ml_prediction": 1,
  "ml_confidence": 0.82,
  "indicators": {
    "rsi": 28.5,
    "macd": 0.0023,
    "bb_position": 0.15,
    "stochastic_k": 25.3,
    "stochastic_d": 30.1
  },
  "gpt_commentary": {
    "market_sentiment": "bullish",
    "key_factors": ["oversold conditions", "momentum shift"],
    "risk_assessment": "moderate"
  },
  "timestamp": "2025-07-20T17:45:30.123456",
  "price": 45000.0
}
```

#### **Autonomous Decision Response**
```json
{
  "action": "buy",
  "reason": "Strong buy signal with 85.0% confidence | GPT Analysis: Confirmed",
  "confidence": 0.935,
  "position_size": 1000.0,
  "risk_level": "low"
}
```

---

## 🔮 **Future Enhancements**

### **Planned Features**
- **Advanced ML Models**: Deep learning and ensemble methods
- **Real-time Streaming**: WebSocket support for live signals
- **Multi-timeframe Analysis**: Signals across different timeframes
- **Sentiment Integration**: Social media sentiment analysis
- **Portfolio Optimization**: Multi-asset signal coordination

### **Performance Improvements**
- **Model Optimization**: Hyperparameter tuning and feature selection
- **Caching**: Redis-based signal and indicator caching
- **Parallel Processing**: Concurrent signal generation
- **Load Balancing**: Multiple agent instances

### **Advanced Capabilities**
- **Predictive Analytics**: Price prediction models
- **Risk Modeling**: Advanced risk assessment algorithms
- **Market Regime Detection**: Bull/bear market identification
- **Anomaly Detection**: Unusual market pattern recognition

---

## ⚠️ **Important Notes**

### **Risk Considerations**
- **Signal Accuracy**: No guarantee of profitable trades
- **Market Conditions**: Performance varies with market conditions
- **Model Limitations**: ML models based on historical data
- **Confidence Levels**: Higher confidence doesn't guarantee success
- **Risk Management**: Always use proper position sizing and stop losses

### **Best Practices**
- **Model Validation**: Regularly validate model performance
- **Signal Confirmation**: Use multiple timeframes for confirmation
- **Risk Management**: Implement proper risk controls
- **Monitoring**: Continuously monitor signal quality
- **Backtesting**: Test strategies before live trading

### **Limitations**
- **Historical Bias**: Models trained on historical data
- **Market Changes**: Performance may degrade with market changes
- **Overfitting**: Risk of overfitting to training data
- **Liquidity**: Signals may not work in low-liquidity markets
- **Regulatory**: Compliance with trading regulations required

---

## 📞 **Support**

For issues, questions, or contributions:
- **Documentation**: This file and inline code comments
- **Logs**: Check agent logs for detailed error information
- **Health Checks**: Use `/health` endpoint for status
- **Testing**: Use test endpoints for validation
- **Monitoring**: Monitor signal quality and model performance

---

*Last Updated: 2025-07-20*  
*Version: 1.0.0* 