"""
VolexSwarm Signal Agent - Autonomous AI Trading Signal Generator
Handles autonomous market analysis, signal generation, and decision making.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import asyncio
import aiohttp

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Signal, PriceData, Strategy, Trade
from common.openai_client import get_openai_client, is_openai_available

# Initialize structured logger
logger = get_logger("signal")

app = FastAPI(title="VolexSwarm Signal Agent", version="1.0.0")

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
autonomous_mode = True  # Default to autonomous mode


class TechnicalIndicators:
    """Technical analysis indicators for autonomous signal generation."""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return [50.0] * len(prices)  # Neutral RSI if insufficient data
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = pd.Series(gains).rolling(window=period).mean().values
        avg_losses = pd.Series(losses).rolling(window=period).mean().values
        
        rs = avg_gains / (avg_losses + 1e-10)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        # Pad with neutral RSI for initial period
        return [50.0] * period + rsi[period:].tolist()
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow:
            return [0.0] * len(prices), [0.0] * len(prices), [0.0] * len(prices)
        
        prices_series = pd.Series(prices)
        ema_fast = prices_series.ewm(span=fast).mean().values
        ema_slow = prices_series.ewm(span=slow).mean().values
        
        macd_line = ema_fast - ema_slow
        signal_line = pd.Series(macd_line).ewm(span=signal).mean().values
        histogram = macd_line - signal_line
        
        return macd_line.tolist(), signal_line.tolist(), histogram.tolist()
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return prices, prices, prices
        
        prices_series = pd.Series(prices)
        sma = prices_series.rolling(window=period).mean().values
        std = prices_series.rolling(window=period).std().values
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band.tolist(), sma.tolist(), lower_band.tolist()
    
    @staticmethod
    def calculate_stochastic(prices: List[float], period: int = 14) -> Tuple[List[float], List[float]]:
        """Calculate Stochastic Oscillator."""
        if len(prices) < period:
            return [50.0] * len(prices), [50.0] * len(prices)
        
        prices_series = pd.Series(prices)
        lowest_low = prices_series.rolling(window=period).min().values
        highest_high = prices_series.rolling(window=period).max().values
        
        k_percent = 100 * ((prices_series.values - lowest_low) / (highest_high - lowest_low + 1e-10))
        d_percent = pd.Series(k_percent).rolling(window=3).mean().values
        
        return k_percent.tolist(), d_percent.tolist()


class AutonomousSignalAgent:
    """Autonomous AI agent for generating trading signals."""
    
    def __init__(self):
        self.models = {}  # ML models for each symbol
        self.scalers = {}  # Feature scalers
        self.signal_history = {}  # Recent signals for each symbol
        self.confidence_threshold = 0.7  # Minimum confidence for autonomous decisions
        self.max_positions = 3  # Maximum concurrent positions
        self.position_sizing = 0.1  # Position size as fraction of portfolio
        
    def extract_features(self, prices: List[float], volumes: List[float] = None) -> np.ndarray:
        """Extract features for machine learning model."""
        if len(prices) < 50:
            return np.array([])
        
        # Calculate technical indicators
        rsi = self.calculate_rsi(prices)
        macd_line, macd_signal, macd_hist = self.calculate_macd(prices)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(prices)
        stoch_k, stoch_d = self.calculate_stochastic(prices)
        
        # Price-based features
        price_changes = np.diff(prices)
        price_momentum = prices[-1] / prices[-5] - 1 if len(prices) >= 5 else 0
        price_volatility = np.std(price_changes[-20:]) if len(price_changes) >= 20 else 0
        
        # Volume features (if available)
        volume_features = []
        if volumes and len(volumes) >= 20:
            avg_volume = np.mean(volumes[-20:])
            current_volume = volumes[-1] if volumes else avg_volume
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            volume_features = [volume_ratio, np.std(volumes[-20:]) / avg_volume if avg_volume > 0 else 0]
        else:
            volume_features = [1.0, 0.0]
        
        # Technical indicator features
        features = [
            rsi[-1] if rsi else 50.0,
            macd_line[-1] if macd_line else 0.0,
            macd_hist[-1] if macd_hist else 0.0,
            (prices[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1] + 1e-10) if bb_upper and bb_lower else 0.5,
            stoch_k[-1] if stoch_k else 50.0,
            stoch_d[-1] if stoch_d else 50.0,
            price_momentum,
            price_volatility,
            *volume_features
        ]
        
        return np.array(features)
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate RSI using TechnicalIndicators."""
        return TechnicalIndicators.calculate_rsi(prices, period)
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD using TechnicalIndicators."""
        return TechnicalIndicators.calculate_macd(prices, fast, slow, signal)
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2.0):
        """Calculate Bollinger Bands using TechnicalIndicators."""
        return TechnicalIndicators.calculate_bollinger_bands(prices, period, std_dev)
    
    def calculate_stochastic(self, prices: List[float], period: int = 14):
        """Calculate Stochastic using TechnicalIndicators."""
        return TechnicalIndicators.calculate_stochastic(prices, period)
    
    def train_model(self, symbol: str, historical_data: List[Dict[str, Any]]) -> bool:
        """Train machine learning model for a symbol."""
        try:
            if len(historical_data) < 100:
                logger.warning(f"Insufficient data for training model: {symbol}")
                return False
            
            # Prepare training data
            prices = [d['close'] for d in historical_data]
            volumes = [d.get('volume', 0) for d in historical_data]
            
            # Create labels (1 for buy, 0 for hold, -1 for sell)
            labels = []
            for i in range(len(prices) - 1):
                future_return = (prices[i + 1] - prices[i]) / prices[i]
                if future_return > 0.02:  # 2% gain threshold
                    labels.append(1)
                elif future_return < -0.02:  # 2% loss threshold
                    labels.append(-1)
                else:
                    labels.append(0)
            
            # Extract features
            features_list = []
            valid_labels = []
            
            for i in range(50, len(prices) - 1):
                features = self.extract_features(prices[:i+1], volumes[:i+1])
                if len(features) > 0:
                    features_list.append(features)
                    valid_labels.append(labels[i-50])
            
            if len(features_list) < 50:
                logger.warning(f"Insufficient features for training: {symbol}")
                return False
            
            # Train model
            X = np.array(features_list)
            y = np.array(valid_labels)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train Random Forest
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_scaled, y)
            
            # Store model and scaler
            self.models[symbol] = model
            self.scalers[symbol] = scaler
            
            logger.info(f"Model trained successfully for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train model for {symbol}: {e}")
            return False
    
    def generate_signal(self, symbol: str, current_data: Dict[str, Any], 
                       historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate autonomous trading signal with GPT-enhanced reasoning."""
        try:
            # Extract current price and features
            current_price = current_data['close']
            prices = [d['close'] for d in historical_data]
            volumes = [d.get('volume', 0) for d in historical_data]
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(prices)
            macd_line, macd_signal, macd_hist = self.calculate_macd(prices)
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(prices)
            stoch_k, stoch_d = self.calculate_stochastic(prices)
            
            # Technical analysis signals
            technical_signals = []
            signal_strength = 0.0
            
            # RSI signals
            if rsi and len(rsi) > 0:
                current_rsi = rsi[-1]
                if current_rsi < 30:
                    technical_signals.append(("RSI oversold", 0.8))
                    signal_strength += 0.3
                elif current_rsi > 70:
                    technical_signals.append(("RSI overbought", -0.8))
                    signal_strength -= 0.3
            
            # MACD signals
            if macd_line and macd_signal and len(macd_line) > 1:
                if macd_line[-1] > macd_signal[-1] and macd_line[-2] <= macd_signal[-2]:
                    technical_signals.append(("MACD bullish crossover", 0.6))
                    signal_strength += 0.2
                elif macd_line[-1] < macd_signal[-1] and macd_line[-2] >= macd_signal[-2]:
                    technical_signals.append(("MACD bearish crossover", -0.6))
                    signal_strength -= 0.2
            
            # Bollinger Bands signals
            if bb_upper and bb_lower and len(bb_upper) > 0:
                bb_position = (current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1] + 1e-10)
                if bb_position < 0.2:
                    technical_signals.append(("BB oversold", 0.7))
                    signal_strength += 0.25
                elif bb_position > 0.8:
                    technical_signals.append(("BB overbought", -0.7))
                    signal_strength -= 0.25
            
            # ML model prediction
            ml_confidence = 0.0
            ml_prediction = 0
            
            if symbol in self.models and len(prices) >= 50:
                try:
                    features = self.extract_features(prices, volumes)
                    if len(features) > 0:
                        features_scaled = self.scalers[symbol].transform([features])
                        prediction = self.models[symbol].predict(features_scaled)[0]
                        probabilities = self.models[symbol].predict_proba(features_scaled)[0]
                        ml_confidence = max(probabilities)
                        ml_prediction = prediction
                        
                        if ml_confidence > self.confidence_threshold:
                            if prediction == 1:
                                signal_strength += 0.4
                                technical_signals.append(("ML buy signal", 0.8))
                            elif prediction == -1:
                                signal_strength -= 0.4
                                technical_signals.append(("ML sell signal", -0.8))
                except Exception as e:
                    logger.warning(f"ML prediction failed for {symbol}: {e}")
            
            # Determine final signal
            signal_type = "hold"
            confidence = abs(signal_strength)
            
            if signal_strength > 0.5:
                signal_type = "buy"
            elif signal_strength < -0.5:
                signal_type = "sell"
            
            # Prepare technical indicators for GPT analysis
            technical_indicators = {
                'rsi': rsi[-1] if rsi else 50.0,
                'macd': macd_line[-1] if macd_line else 0.0,
                'bb_position': (current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1] + 1e-10) if bb_upper and bb_lower else 0.5,
                'stochastic_k': stoch_k[-1] if stoch_k else 50.0,
                'stochastic_d': stoch_d[-1] if stoch_d else 50.0
            }
            
            # Prepare price data for GPT analysis
            price_data = {
                'close': current_price,
                'change_24h': ((current_price - prices[-24]) / prices[-24] * 100) if len(prices) >= 24 else 0,
                'volume': volumes[-1] if volumes else 0
            }
            
            # Generate GPT-enhanced market commentary
            gpt_commentary = {}
            if is_openai_available():
                try:
                    openai_client = get_openai_client()
                    gpt_commentary = openai_client.generate_market_commentary(
                        symbol=symbol,
                        price_data=price_data,
                        technical_indicators=technical_indicators
                    )
                except Exception as e:
                    logger.warning(f"GPT commentary generation failed: {e}")
            
            # Autonomous decision making with GPT enhancement
            autonomous_decision = {
                'signal_type': signal_type,
                'confidence': min(confidence, 1.0),
                'strength': signal_strength,
                'technical_signals': technical_signals,
                'ml_prediction': ml_prediction,
                'ml_confidence': ml_confidence,
                'indicators': technical_indicators,
                'gpt_commentary': gpt_commentary,
                'timestamp': datetime.now(),
                'price': current_price
            }
            
            # Store signal history
            if symbol not in self.signal_history:
                self.signal_history[symbol] = []
            self.signal_history[symbol].append(autonomous_decision)
            
            # Keep only recent signals
            if len(self.signal_history[symbol]) > 100:
                self.signal_history[symbol] = self.signal_history[symbol][-100:]
            
            return autonomous_decision
            
        except Exception as e:
            logger.error(f"Failed to generate signal for {symbol}: {e}")
            return {
                'signal_type': 'hold',
                'confidence': 0.0,
                'strength': 0.0,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def get_signal_history(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get signal history for a symbol."""
        if symbol in self.signal_history:
            return self.signal_history[symbol][-limit:]
        return []
    
    def get_autonomous_insights(self, symbol: str) -> Dict[str, Any]:
        """Get autonomous AI insights for a symbol."""
        if symbol not in self.signal_history or not self.signal_history[symbol]:
            return {'insights': 'No signal history available'}
        
        recent_signals = self.signal_history[symbol][-20:]
        
        # Analyze signal patterns
        buy_signals = [s for s in recent_signals if s['signal_type'] == 'buy']
        sell_signals = [s for s in recent_signals if s['signal_type'] == 'sell']
        
        avg_buy_confidence = np.mean([s['confidence'] for s in buy_signals]) if buy_signals else 0
        avg_sell_confidence = np.mean([s['confidence'] for s in sell_signals]) if sell_signals else 0
        
        # Trend analysis
        signal_strengths = [s['strength'] for s in recent_signals]
        trend = np.mean(signal_strengths) if signal_strengths else 0
        
        # Volatility analysis
        confidences = [s['confidence'] for s in recent_signals]
        volatility = np.std(confidences) if len(confidences) > 1 else 0
        
        insights = {
            'trend': 'bullish' if trend > 0.2 else 'bearish' if trend < -0.2 else 'neutral',
            'trend_strength': abs(trend),
            'buy_signals_count': len(buy_signals),
            'sell_signals_count': len(sell_signals),
            'avg_buy_confidence': avg_buy_confidence,
            'avg_sell_confidence': avg_sell_confidence,
            'signal_volatility': volatility,
            'recommendation': self._generate_recommendation(trend, avg_buy_confidence, avg_sell_confidence),
            'last_updated': datetime.now().isoformat()
        }
        
        return insights
    
    def _generate_recommendation(self, trend: float, buy_conf: float, sell_conf: float) -> str:
        """Generate autonomous recommendation."""
        if trend > 0.3 and buy_conf > 0.7:
            return "Strong buy - Multiple indicators align for upward movement"
        elif trend > 0.1 and buy_conf > 0.6:
            return "Buy - Positive trend with good confidence"
        elif trend < -0.3 and sell_conf > 0.7:
            return "Strong sell - Multiple indicators align for downward movement"
        elif trend < -0.1 and sell_conf > 0.6:
            return "Sell - Negative trend with good confidence"
        elif abs(trend) < 0.1:
            return "Hold - Market is neutral, wait for clearer signals"
        else:
            return "Monitor - Mixed signals, exercise caution"


# Global signal agent
signal_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize the signal agent on startup."""
    global vault_client, db_client, signal_agent, autonomous_mode
    
    try:
        with logger.log_operation("signal_agent_startup"):
            # Initialize Vault client
            vault_client = get_vault_client()
            logger.info("Vault client initialized successfully")
            
            # Initialize database client
            db_client = get_db_client()
            logger.info("Database client initialized successfully")
            
            # Load agent configuration
            config = get_agent_config("signal")
            if config:
                logger.info("Loaded configuration for signal agent", config)
                autonomous_mode = config.get('autonomous_mode', True)
            
            # Initialize autonomous signal agent
            signal_agent = AutonomousSignalAgent()
            
            # Load pre-trained models if available
            await load_models()
            
            logger.info("Signal agent initialized successfully")
            logger.info(f"Autonomous mode: {autonomous_mode}")
        
    except Exception as e:
        logger.error("Failed to initialize signal agent", exception=e)
        raise


async def load_models():
    """Load pre-trained models from database or files."""
    try:
        # This would load models from persistent storage
        # For now, we'll train models on-demand
        logger.info("Models will be trained on-demand")
    except Exception as e:
        logger.warning(f"Failed to load models: {e}")


@app.get("/health")
def health_check():
    """Detailed health check including autonomous capabilities."""
    try:
        vault_healthy = vault_client.health_check() if vault_client else False
        db_healthy = db_health_check() if db_client else False
        agent_ready = signal_agent is not None
        
        overall_healthy = vault_healthy and db_healthy and agent_ready
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "vault_connected": vault_healthy,
            "database_connected": db_healthy,
            "agent_ready": agent_ready,
            "autonomous_mode": autonomous_mode,
            "models_loaded": len(signal_agent.models) if signal_agent else 0,
            "agent": "signal"
        }
    except Exception as e:
        logger.error("Health check failed", exception=e)
        return {
            "status": "unhealthy",
            "vault_connected": False,
            "database_connected": False,
            "agent_ready": False,
            "error": str(e),
            "agent": "signal"
        }


@app.post("/signals/generate")
def generate_signal(symbol: str, strategy_id: Optional[int] = None):
    """Generate autonomous trading signal for a symbol."""
    try:
        if not signal_agent:
            raise HTTPException(status_code=500, detail="Signal agent not initialized")
        
        with logger.log_operation("generate_signal", {"symbol": symbol, "strategy_id": strategy_id}):
            # Get historical data from database
            if not db_client:
                raise HTTPException(status_code=500, detail="Database not connected")
            
            session = db_client.get_session()
            
            # Get recent price data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)  # 30 days of data
            
            price_data = session.query(PriceData).filter(
                PriceData.symbol == symbol,
                PriceData.time >= start_time,
                PriceData.time <= end_time
            ).order_by(PriceData.time.asc()).all()
            
            if len(price_data) < 50:
                raise HTTPException(status_code=400, detail=f"Insufficient data for {symbol}")
            
            # Convert to format expected by signal agent
            historical_data = []
            for data in price_data:
                historical_data.append({
                    'close': data.close,
                    'open': data.open,
                    'high': data.high,
                    'low': data.low,
                    'volume': data.volume,
                    'time': data.time
                })
            
            current_data = historical_data[-1]
            
            # Generate autonomous signal
            signal_result = signal_agent.generate_signal(symbol, current_data, historical_data)
            
            # Store signal in database
            if signal_result['signal_type'] != 'hold':
                # Convert numpy types to native Python types for JSON serialization
                indicators = {}
                for key, value in signal_result['indicators'].items():
                    if hasattr(value, 'item'):
                        indicators[key] = value.item()
                    else:
                        indicators[key] = value
                
                signal_metadata = {
                    'autonomous': True,
                    'technical_signals': signal_result['technical_signals'],
                    'ml_prediction': int(signal_result['ml_prediction']) if hasattr(signal_result['ml_prediction'], 'item') else signal_result['ml_prediction'],
                    'ml_confidence': float(signal_result['ml_confidence']) if hasattr(signal_result['ml_confidence'], 'item') else signal_result['ml_confidence']
                }
                
                signal = Signal(
                    timestamp=signal_result['timestamp'],
                    strategy_id=strategy_id,
                    symbol=symbol,
                    signal_type=signal_result['signal_type'],
                    strength=float(signal_result['strength']),
                    confidence=float(signal_result['confidence']),
                    timeframe='1h',
                    indicators=indicators,
                    signal_metadata=signal_metadata
                )
                session.add(signal)
                session.commit()
                
                logger.log_signal({
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type,
                    'confidence': signal.confidence,
                    'strength': signal.strength,
                    'autonomous': True
                })
            
            session.close()
            
            # Convert numpy types to native Python types for JSON serialization
            def convert_numpy_types(obj):
                if hasattr(obj, 'item'):
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                else:
                    return obj
            
            # Convert signal_result to ensure JSON serializable
            serializable_signal = convert_numpy_types(signal_result)
            
            return {
                "agent": "signal",
                "symbol": symbol,
                "signal": serializable_signal,
                "autonomous": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate signal", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals")
def get_signals(symbol: Optional[str] = None, limit: int = 50):
    """Get signal history."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        session = db_client.get_session()
        
        query = session.query(Signal)
        if symbol:
            query = query.filter(Signal.symbol == symbol)
        
        signals = query.order_by(Signal.timestamp.desc()).limit(limit).all()
        
        result = []
        for signal in signals:
            result.append({
                'timestamp': signal.timestamp.isoformat(),
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'strength': signal.strength,
                'confidence': signal.confidence,
                'timeframe': signal.timeframe,
                'strategy_id': signal.strategy_id,
                'indicators': signal.indicators,
                'autonomous': signal.signal_metadata.get('autonomous', False) if signal.signal_metadata else False
            })
        
        session.close()
        
        return {
            "agent": "signal",
            "signals": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error("Failed to get signals", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/indicators/{symbol}")
def get_indicators(symbol: str, timeframe: str = "1h"):
    """Get current technical indicators for a symbol."""
    try:
        if not signal_agent or not db_client:
            raise HTTPException(status_code=500, detail="Agent or database not initialized")
        
        session = db_client.get_session()
        
        # Get recent price data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        price_data = session.query(PriceData).filter(
            PriceData.symbol == symbol,
            PriceData.timeframe == timeframe,
            PriceData.time >= start_time,
            PriceData.time <= end_time
        ).order_by(PriceData.time.asc()).all()
        
        if len(price_data) < 20:
            raise HTTPException(status_code=400, detail=f"Insufficient data for {symbol}")
        
        prices = [d.close for d in price_data]
        
        # Calculate indicators
        rsi = signal_agent.calculate_rsi(prices)
        macd_line, macd_signal, macd_hist = signal_agent.calculate_macd(prices)
        bb_upper, bb_middle, bb_lower = signal_agent.calculate_bollinger_bands(prices)
        stoch_k, stoch_d = signal_agent.calculate_stochastic(prices)
        
        current_price = prices[-1]
        
        session.close()
        
        return {
            "agent": "signal",
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": current_price,
            "indicators": {
                "rsi": rsi[-1] if rsi else None,
                "macd": {
                    "line": macd_line[-1] if macd_line else None,
                    "signal": macd_signal[-1] if macd_signal else None,
                    "histogram": macd_hist[-1] if macd_hist else None
                },
                "bollinger_bands": {
                    "upper": bb_upper[-1] if bb_upper else None,
                    "middle": bb_middle[-1] if bb_middle else None,
                    "lower": bb_lower[-1] if bb_lower else None,
                    "position": (current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1] + 1e-10) if bb_upper and bb_lower else None
                },
                "stochastic": {
                    "k": stoch_k[-1] if stoch_k else None,
                    "d": stoch_d[-1] if stoch_d else None
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get indicators", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/train")
def train_model(symbol: str):
    """Train machine learning model for a symbol."""
    try:
        if not signal_agent or not db_client:
            raise HTTPException(status_code=500, detail="Agent or database not initialized")
        
        with logger.log_operation("train_model", {"symbol": symbol}):
            session = db_client.get_session()
            
            # Get historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=90)  # 90 days for training
            
            price_data = session.query(PriceData).filter(
                PriceData.symbol == symbol,
                PriceData.time >= start_time,
                PriceData.time <= end_time
            ).order_by(PriceData.time.asc()).all()
            
            if len(price_data) < 100:
                raise HTTPException(status_code=400, detail=f"Insufficient data for training: {symbol}")
            
            # Convert to format expected by signal agent
            historical_data = []
            for data in price_data:
                historical_data.append({
                    'close': data.close,
                    'open': data.open,
                    'high': data.high,
                    'low': data.low,
                    'volume': data.volume,
                    'time': data.time
                })
            
            # Train model
            success = signal_agent.train_model(symbol, historical_data)
            
            session.close()
            
            if success:
                return {
                    "agent": "signal",
                    "symbol": symbol,
                    "status": "success",
                    "message": f"Model trained successfully for {symbol}",
                    "data_points": len(historical_data)
                }
            else:
                raise HTTPException(status_code=500, detail=f"Failed to train model for {symbol}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to train model", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/performance")
def get_model_performance():
    """Get performance metrics for trained models."""
    try:
        if not signal_agent:
            raise HTTPException(status_code=500, detail="Signal agent not initialized")
        
        performance = {}
        
        for symbol in signal_agent.models.keys():
            insights = signal_agent.get_autonomous_insights(symbol)
            performance[symbol] = {
                'model_trained': True,
                'insights': insights,
                'signal_count': len(signal_agent.get_signal_history(symbol))
            }
        
        return {
            "agent": "signal",
            "models": performance,
            "total_models": len(signal_agent.models),
            "autonomous_mode": autonomous_mode
        }
        
    except Exception as e:
        logger.error("Failed to get model performance", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/autonomous/insights/{symbol}")
def get_autonomous_insights(symbol: str):
    """Get autonomous AI insights for a symbol."""
    try:
        if not signal_agent:
            raise HTTPException(status_code=500, detail="Signal agent not initialized")
        
        insights = signal_agent.get_autonomous_insights(symbol)
        
        return {
            "agent": "signal",
            "symbol": symbol,
            "insights": insights,
            "autonomous": True
        }
        
    except Exception as e:
        logger.error("Failed to get autonomous insights", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/autonomous/decide")
def autonomous_decision(symbol: str, current_balance: float = 10000.0):
    """Make autonomous trading decision with GPT-enhanced reasoning."""
    try:
        if not signal_agent:
            raise HTTPException(status_code=500, detail="Signal agent not initialized")
        
        if not autonomous_mode:
            raise HTTPException(status_code=400, detail="Autonomous mode is disabled")
        
        with logger.log_operation("autonomous_decision", {"symbol": symbol, "balance": current_balance}):
            # Generate signal
            signal_response = generate_signal(symbol)
            signal_data = signal_response['signal']
            
            # Prepare market data for GPT analysis
            market_data = {
                'symbol': symbol,
                'current_price': signal_data.get('price', 0),
                'indicators': signal_data.get('indicators', {}),
                'technical_signals': signal_data.get('technical_signals', [])
            }
            
            # Prepare risk parameters
            risk_parameters = {
                'current_balance': current_balance,
                'max_position_size': 0.1,  # 10% of portfolio
                'stop_loss_percentage': 0.05,  # 5% stop loss
                'max_risk_per_trade': 0.02  # 2% max risk per trade
            }
            
            # Make initial autonomous decision
            decision = {
                'action': 'hold',
                'reason': 'No clear signal',
                'confidence': 0.0,
                'position_size': 0.0,
                'risk_level': 'low'
            }
            
            # Make initial decision based on signal
            proposed_action = 'hold'
            if signal_data['signal_type'] == 'buy' and signal_data['confidence'] > 0.7:
                proposed_action = 'buy'
                decision.update({
                    'action': 'buy',
                    'reason': f"Strong buy signal with {signal_data['confidence']:.1%} confidence",
                    'confidence': signal_data['confidence'],
                    'position_size': current_balance * signal_agent.position_sizing,
                    'risk_level': 'medium' if signal_data['confidence'] < 0.8 else 'low'
                })
            elif signal_data['signal_type'] == 'sell' and signal_data['confidence'] > 0.7:
                proposed_action = 'sell'
                decision.update({
                    'action': 'sell',
                    'reason': f"Strong sell signal with {signal_data['confidence']:.1%} confidence",
                    'confidence': signal_data['confidence'],
                    'position_size': current_balance * signal_agent.position_sizing,
                    'risk_level': 'medium' if signal_data['confidence'] < 0.8 else 'low'
                })
            elif signal_data['signal_type'] != 'hold':
                proposed_action = signal_data['signal_type']
                decision.update({
                    'action': signal_data['signal_type'],
                    'reason': f"Weak {signal_data['signal_type']} signal with {signal_data['confidence']:.1%} confidence",
                    'confidence': signal_data['confidence'],
                    'position_size': current_balance * signal_agent.position_sizing * 0.5,  # Smaller position
                    'risk_level': 'high'
                })
            
            # Enhance decision with GPT analysis if available
            gpt_analysis = {}
            if is_openai_available() and proposed_action != 'hold':
                try:
                    openai_client = get_openai_client()
                    gpt_analysis = openai_client.analyze_trading_decision(
                        symbol=symbol,
                        proposed_action=proposed_action,
                        signal_data=signal_data,
                        market_data=market_data,
                        risk_parameters=risk_parameters
                    )
                    
                    # Update decision based on GPT analysis
                    if gpt_analysis.get('recommendation') == 'confirm':
                        # GPT confirms the decision
                        decision['reason'] += f" | GPT Analysis: {gpt_analysis.get('reasoning', 'Confirmed')}"
                        decision['confidence'] = min(decision['confidence'] * 1.1, 1.0)  # Boost confidence slightly
                    elif gpt_analysis.get('recommendation') == 'modify':
                        # GPT suggests modification
                        decision['reason'] += f" | GPT Analysis: {gpt_analysis.get('reasoning', 'Modification suggested')}"
                        decision['position_size'] *= 0.8  # Reduce position size
                        decision['risk_level'] = 'high'
                    elif gpt_analysis.get('recommendation') == 'reject':
                        # GPT rejects the decision
                        decision.update({
                            'action': 'hold',
                            'reason': f"GPT Analysis: {gpt_analysis.get('reasoning', 'Decision rejected')}",
                            'confidence': 0.0,
                            'position_size': 0.0,
                            'risk_level': 'high'
                        })
                    
                except Exception as e:
                    logger.warning(f"GPT decision analysis failed: {e}")
            
            # Convert numpy types to native Python types for JSON serialization
            def convert_numpy_types(obj):
                if hasattr(obj, 'item'):
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                else:
                    return obj
            
            # Convert signal_data to ensure JSON serializable
            serializable_signal = convert_numpy_types(signal_data)
            
            # Add GPT analysis to response
            response_data = {
                "agent": "signal",
                "symbol": symbol,
                "decision": decision,
                "signal": serializable_signal,
                "autonomous": True,
                "gpt_analysis": gpt_analysis,
                "openai_available": is_openai_available(),
                "timestamp": datetime.now().isoformat()
            }
            
            return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to make autonomous decision", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 