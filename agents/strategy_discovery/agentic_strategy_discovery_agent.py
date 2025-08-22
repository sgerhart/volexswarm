#!/usr/bin/env python3
"""
Strategy Discovery Agent for VolexSwarm
AI-powered strategy discovery and pattern recognition system.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import ccxt
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from sqlalchemy.orm import Session

# Add the parent directory to the path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.db import DatabaseClient, get_session
from common.models import Strategy, PriceData, Signal, Backtest, PerformanceMetrics, ProductionStrategy
from common.vault import get_exchange_credentials, get_vault_client
from agents.agentic_framework.agent_templates import BaseAgent, AgentConfig
from agents.agentic_framework.mcp_tools import MCPTool, MCPToolRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyDiscoveryTools:
    """Tools for strategy discovery and pattern recognition."""
    
    def __init__(self):
        self.tools = {
            "analyze_market_patterns": self.analyze_market_patterns,
            "generate_strategy_candidates": self.generate_strategy_candidates,
            "evaluate_strategy_performance": self.evaluate_strategy_performance,
            "detect_risk_profile": self.detect_risk_profile,
            "optimize_strategy_parameters": self.optimize_strategy_parameters,
            "rank_strategies": self.rank_strategies,
            "create_sandbox_test": self.create_sandbox_test,
                                    "analyze_cross_asset_correlations": self.analyze_cross_asset_correlations,
                        "detect_market_regimes": self.detect_market_regimes,
                        "generate_ml_strategies": self.generate_ml_strategies,
                        "manage_exchange_credentials": self.manage_exchange_credentials,
                        "list_exchange_credentials": self.list_exchange_credentials,
                        "test_exchange_connection": self.test_exchange_connection,
                        "explain_strategy_results": self.explain_strategy_results,
                        "explain_market_conditions": self.explain_market_conditions,
                        "explain_performance_metrics": self.explain_performance_metrics,
                        "generate_user_summary": self.generate_user_summary,
                        "evaluate_strategy_for_promotion": self.evaluate_strategy_for_promotion,
                        "promote_strategy_to_production": self.promote_strategy_to_production,
                        "manage_strategy_lifecycle": self.manage_strategy_lifecycle,
                        "monitor_strategy_performance": self.monitor_strategy_performance,
                        "deactivate_strategy": self.deactivate_strategy,
        }
    
    async def analyze_market_patterns(self, symbol: str, timeframe: str = "1d", lookback_days: int = 365) -> Dict[str, Any]:
        """Analyze market patterns for a given symbol."""
        try:
            # First try to get data from database
            df = await self._get_historical_data_from_db(symbol, timeframe, lookback_days)
            
            # If no data in database, fetch from Binance US
            if df is None or df.empty:
                logger.info(f"No data in database for {symbol}, fetching from Binance US...")
                df = await self._fetch_historical_data_from_binance(symbol, timeframe, lookback_days)
                
                if df is None or df.empty:
                    return {"error": f"No price data found for {symbol}"}
                
                # Store the data in database for future use
                await self._store_historical_data_to_db(symbol, timeframe, df)
            
            # Calculate technical indicators
            patterns = self._calculate_patterns(df)
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "patterns": patterns,
                "data_points": len(df),
                "date_range": {
                    "start": df['time'].min().isoformat() if not df.empty else None,
                    "end": df['time'].max().isoformat() if not df.empty else None
                },
                "data_source": "binanceus" if df is not None and not df.empty else "database"
            }
                
        except Exception as e:
            logger.error(f"Error analyzing market patterns: {e}")
            return {"error": str(e)}
    
    async def _get_historical_data_from_db(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        """Get historical data from database."""
        try:
            with get_session() as session:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=lookback_days)
                
                price_data = session.query(PriceData).filter(
                    PriceData.symbol == symbol,
                    PriceData.timeframe == timeframe,
                    PriceData.time >= start_date,
                    PriceData.time <= end_date
                ).order_by(PriceData.time).all()
                
                if not price_data:
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame([{
                    'time': p.time,
                    'open': p.open,
                    'high': p.high,
                    'low': p.low,
                    'close': p.close,
                    'volume': p.volume
                } for p in price_data])
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting historical data from DB: {e}")
            return None
    
    async def _fetch_historical_data_from_binance(self, symbol: str, timeframe: str, lookback_days: int) -> Optional[pd.DataFrame]:
        """Fetch historical data from Binance."""
        try:
            # Try to get Binance US credentials from Vault
            credentials = get_exchange_credentials("binance")
            
            if credentials:
                # Initialize Binance US exchange with authenticated API
                logger.info(f"Using authenticated Binance US API for {symbol}")
                exchange = ccxt.binanceus({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret_key'),
                    'sandbox': False,  # Use live data
                    'enableRateLimit': True,
                })
            else:
                # Use public Binance US API (no authentication required)
                logger.info(f"Using public Binance US API for {symbol} (no credentials)")
                exchange = ccxt.binanceus({
                    'enableRateLimit': True,
                })
            
            # Convert timeframe to Binance format
            timeframe_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"
            }
            binance_timeframe = timeframe_map.get(timeframe, "1d")
            
            # Calculate timestamps
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=lookback_days)).timestamp() * 1000)
            
            # Fetch OHLCV data
            ohlcv = exchange.fetch_ohlcv(symbol, binance_timeframe, start_time, limit=1000)
            
            if not ohlcv:
                logger.error(f"No data returned from Binance US for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.drop('timestamp', axis=1)
            
            logger.info(f"Fetched {len(df)} data points from Binance US for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from Binance US: {e}")
            logger.info(f"Generating sample data for {symbol} for testing purposes")
            return self._generate_sample_data(symbol, timeframe, lookback_days)
    
    def _generate_sample_data(self, symbol: str, timeframe: str, lookback_days: int) -> pd.DataFrame:
        """Generate sample price data for testing when Binance is unavailable."""
        try:
            # Generate realistic sample data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            # Create date range
            if timeframe == "1d":
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            elif timeframe == "1h":
                date_range = pd.date_range(start=start_date, end=end_date, freq='H')
            elif timeframe == "4h":
                date_range = pd.date_range(start=start_date, end=end_date, freq='4H')
            else:
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Generate realistic price data
            np.random.seed(42)  # For reproducible results
            
            # Base price (realistic for crypto)
            if "BTC" in symbol:
                base_price = 45000
            elif "ETH" in symbol:
                base_price = 3000
            else:
                base_price = 100
            
            # Generate price series with trend and volatility
            n_periods = len(date_range)
            returns = np.random.normal(0.001, 0.02, n_periods)  # Daily returns with volatility
            
            # Add some trend
            trend = np.linspace(0, 0.1, n_periods)  # 10% upward trend over the period
            returns += trend / n_periods
            
            # Calculate prices
            prices = [base_price]
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            # Generate OHLCV data
            data = []
            for i, (date, price) in enumerate(zip(date_range, prices)):
                # Generate realistic OHLC from close price
                volatility = 0.02  # 2% daily volatility
                high = price * (1 + abs(np.random.normal(0, volatility)))
                low = price * (1 - abs(np.random.normal(0, volatility)))
                open_price = prices[i-1] if i > 0 else price
                volume = np.random.uniform(1000, 10000)
                
                data.append({
                    'time': date,
                    'open': open_price,
                    'high': max(high, open_price, price),
                    'low': min(low, open_price, price),
                    'close': price,
                    'volume': volume
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Generated {len(df)} sample data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error generating sample data: {e}")
            return pd.DataFrame()
    
    async def _store_historical_data_to_db(self, symbol: str, timeframe: str, df: pd.DataFrame) -> bool:
        """Store historical data to database."""
        try:
            with get_session() as session:
                for _, row in df.iterrows():
                    # Check if data already exists
                    existing = session.query(PriceData).filter(
                        PriceData.symbol == symbol,
                        PriceData.timeframe == timeframe,
                        PriceData.time == row['time']
                    ).first()
                    
                    if not existing:
                        price_data = PriceData(
                            symbol=symbol,
                            timeframe=timeframe,
                            time=row['time'],
                            open=row['open'],
                            high=row['high'],
                            low=row['low'],
                            close=row['close'],
                            volume=row['volume'],
                            exchange='binanceus'
                        )
                        session.add(price_data)
                
                session.commit()
                logger.info(f"Stored {len(df)} data points to database for {symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing data to database: {e}")
            return False
    
    def _calculate_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate various market patterns."""
        patterns = {}
        
        # Price patterns
        patterns["price_trend"] = self._calculate_price_trend(df)
        patterns["volatility_patterns"] = self._calculate_volatility_patterns(df)
        patterns["volume_patterns"] = self._calculate_volume_patterns(df)
        patterns["support_resistance"] = self._calculate_support_resistance(df)
        patterns["candlestick_patterns"] = self._calculate_candlestick_patterns(df)
        
        return patterns
    
    def _calculate_price_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate price trend patterns."""
        df = df.copy()
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # Trend indicators
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['rsi'] = self._calculate_rsi(df['close'])
        
        # Current trend analysis
        current_price = df['close'].iloc[-1]
        sma_20 = df['sma_20'].iloc[-1]
        sma_50 = df['sma_50'].iloc[-1]
        
        trend_strength = 0
        if current_price > sma_20 > sma_50:
            trend_strength = 1  # Strong uptrend
        elif current_price > sma_20 and sma_20 < sma_50:
            trend_strength = 0.5  # Weak uptrend
        elif current_price < sma_20 < sma_50:
            trend_strength = -1  # Strong downtrend
        elif current_price < sma_20 and sma_20 > sma_50:
            trend_strength = -0.5  # Weak downtrend
        else:
            trend_strength = 0  # Sideways
        
        return {
            "trend_strength": trend_strength,
            "current_price": float(current_price),
            "sma_20": float(sma_20),
            "sma_50": float(sma_50),
            "rsi": float(df['rsi'].iloc[-1]),
            "macd": float(df['macd'].iloc[-1]),
            "macd_signal": float(df['macd_signal'].iloc[-1])
        }
    
    def _calculate_volatility_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volatility patterns."""
        df = df.copy()
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # Volatility measures
        df['volatility_20'] = df['returns'].rolling(window=20).std()
        df['atr'] = self._calculate_atr(df)
        
        current_volatility = df['volatility_20'].iloc[-1]
        avg_volatility = df['volatility_20'].mean()
        
        volatility_regime = "normal"
        if current_volatility > avg_volatility * 1.5:
            volatility_regime = "high"
        elif current_volatility < avg_volatility * 0.5:
            volatility_regime = "low"
        
        return {
            "current_volatility": float(current_volatility),
            "avg_volatility": float(avg_volatility),
            "volatility_regime": volatility_regime,
            "atr": float(df['atr'].iloc[-1])
        }
    
    def _calculate_volume_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume patterns."""
        df = df.copy()
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        current_volume_ratio = df['volume_ratio'].iloc[-1]
        
        volume_regime = "normal"
        if current_volume_ratio > 1.5:
            volume_regime = "high"
        elif current_volume_ratio < 0.5:
            volume_regime = "low"
        
        return {
            "current_volume_ratio": float(current_volume_ratio),
            "volume_regime": volume_regime,
            "avg_volume": float(df['volume'].mean())
        }
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        # Simple support/resistance calculation
        recent_highs = df['high'].tail(20).nlargest(3)
        recent_lows = df['low'].tail(20).nsmallest(3)
        
        resistance_levels = recent_highs.tolist()
        support_levels = recent_lows.tolist()
        
        current_price = df['close'].iloc[-1]
        
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)
        nearest_support = max([s for s in support_levels if s < current_price], default=None)
        
        return {
            "resistance_levels": resistance_levels,
            "support_levels": support_levels,
            "nearest_resistance": float(nearest_resistance) if nearest_resistance else None,
            "nearest_support": float(nearest_support) if nearest_support else None,
            "current_price": float(current_price)
        }
    
    def _calculate_candlestick_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate candlestick patterns."""
        patterns = []
        
        for i in range(len(df) - 1):
            current = df.iloc[i]
            previous = df.iloc[i-1] if i > 0 else None
            
            # Doji pattern
            body_size = abs(current['close'] - current['open'])
            total_range = current['high'] - current['low']
            
            if body_size / total_range < 0.1:
                patterns.append("doji")
            
            # Hammer pattern
            if (current['close'] > current['open'] and 
                (current['high'] - current['close']) / (current['close'] - current['open']) < 0.3):
                patterns.append("hammer")
            
            # Shooting star pattern
            if (current['close'] < current['open'] and 
                (current['open'] - current['low']) / (current['open'] - current['close']) < 0.3):
                patterns.append("shooting_star")
        
        return {
            "patterns_found": list(set(patterns)),
            "pattern_count": len(patterns)
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    async def generate_strategy_candidates(self, symbol: str, risk_profile: str = "balanced") -> List[Dict[str, Any]]:
        """Generate strategy candidates based on market patterns."""
        try:
            # Analyze market patterns first
            pattern_analysis = await self.analyze_market_patterns(symbol)
            
            if "error" in pattern_analysis:
                return [{"error": pattern_analysis["error"]}]
            
            strategies = []
            
            # Generate strategies based on patterns
            patterns = pattern_analysis["patterns"]
            
            # Trend following strategies
            if patterns["price_trend"]["trend_strength"] > 0.5:
                strategies.append({
                    "name": f"{symbol}_trend_following",
                    "type": "trend_following",
                    "risk_profile": risk_profile,
                    "description": "Follow the established uptrend",
                    "parameters": {
                        "entry_condition": "price > sma_20",
                        "exit_condition": "price < sma_20",
                        "stop_loss": "2 * atr",
                        "take_profit": "3 * atr"
                    },
                    "confidence": 0.8
                })
            
            # Mean reversion strategies
            if patterns["price_trend"]["rsi"] > 70:
                strategies.append({
                    "name": f"{symbol}_mean_reversion_short",
                    "type": "mean_reversion",
                    "risk_profile": risk_profile,
                    "description": "Short on overbought conditions",
                    "parameters": {
                        "entry_condition": "rsi > 70",
                        "exit_condition": "rsi < 50",
                        "stop_loss": "1.5 * atr",
                        "take_profit": "2 * atr"
                    },
                    "confidence": 0.7
                })
            elif patterns["price_trend"]["rsi"] < 30:
                strategies.append({
                    "name": f"{symbol}_mean_reversion_long",
                    "type": "mean_reversion",
                    "risk_profile": risk_profile,
                    "description": "Long on oversold conditions",
                    "parameters": {
                        "entry_condition": "rsi < 30",
                        "exit_condition": "rsi > 50",
                        "stop_loss": "1.5 * atr",
                        "take_profit": "2 * atr"
                    },
                    "confidence": 0.7
                })
            
            # Volatility breakout strategies
            if patterns["volatility_patterns"]["volatility_regime"] == "high":
                strategies.append({
                    "name": f"{symbol}_volatility_breakout",
                    "type": "breakout",
                    "risk_profile": "aggressive",
                    "description": "Trade volatility breakouts",
                    "parameters": {
                        "entry_condition": "price > resistance_level",
                        "exit_condition": "price < support_level",
                        "stop_loss": "1 * atr",
                        "take_profit": "2 * atr"
                    },
                    "confidence": 0.6
                })
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error generating strategy candidates: {e}")
            return [{"error": str(e)}]
    
    async def detect_risk_profile(self, strategy_data: Dict[str, Any]) -> str:
        """Detect the risk profile of a strategy."""
        try:
            # Analyze strategy characteristics
            volatility = strategy_data.get("volatility", 0)
            max_drawdown = strategy_data.get("max_drawdown", 0)
            sharpe_ratio = strategy_data.get("sharpe_ratio", 0)
            
            # Risk profile classification
            if volatility > 0.3 or max_drawdown > 0.15:
                return "aggressive"
            elif volatility < 0.1 and max_drawdown < 0.05:
                return "conservative"
            else:
                return "balanced"
                
        except Exception as e:
            logger.error(f"Error detecting risk profile: {e}")
            return "balanced"
    
    async def rank_strategies(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank strategies based on multiple criteria."""
        try:
            for strategy in strategies:
                # Calculate strategy score
                score = self._calculate_strategy_score(strategy)
                strategy["score"] = score
            
            # Sort by score (descending)
            ranked_strategies = sorted(strategies, key=lambda x: x.get("score", 0), reverse=True)
            
            return ranked_strategies
            
        except Exception as e:
            logger.error(f"Error ranking strategies: {e}")
            return strategies
    
    def _calculate_strategy_score(self, strategy: Dict[str, Any]) -> float:
        """Calculate a composite score for a strategy."""
        score = 0.0
        
        # Return score (30%)
        if "sharpe_ratio" in strategy:
            score += min(strategy["sharpe_ratio"] / 3.0, 1.0) * 0.3
        
        # Risk score (25%)
        if "max_drawdown" in strategy:
            risk_score = max(0, 1 - strategy["max_drawdown"] / 0.2)  # Penalize high drawdowns
            score += risk_score * 0.25
        
        # Consistency score (20%)
        if "win_rate" in strategy:
            score += min(strategy["win_rate"] / 0.7, 1.0) * 0.2
        
        # Adaptability score (15%)
        if "market_regime_performance" in strategy:
            adaptability = strategy["market_regime_performance"].get("consistency", 0.5)
            score += adaptability * 0.15
        
        # Innovation score (10%)
        if "novelty" in strategy:
            score += strategy["novelty"] * 0.1
        
        return score
    
    async def evaluate_strategy_performance(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the performance of a strategy."""
        # Placeholder implementation
        return {
            "strategy_name": strategy.get("name", "Unknown"),
            "sharpe_ratio": 1.5,
            "max_drawdown": 0.1,
            "win_rate": 0.6,
            "profit_factor": 1.8,
            "total_return": 0.25
        }
    
    async def optimize_strategy_parameters(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize strategy parameters."""
        # Placeholder implementation
        return {
            "strategy_name": strategy.get("name", "Unknown"),
            "optimized_parameters": strategy.get("parameters", {}),
            "improvement": 0.15
        }
    
    async def create_sandbox_test(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sandbox test for a strategy."""
        # Placeholder implementation
        return {
            "test_id": f"sandbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "strategy": strategy,
            "status": "created"
        }
    
    async def analyze_cross_asset_correlations(self, symbols: List[str], timeframe: str = "1d", lookback_days: int = 90) -> Dict[str, Any]:
        """Analyze cross-asset correlations."""
        try:
            correlation_data = {}
            price_data = {}
            
            # Fetch data for all symbols
            for symbol in symbols:
                df = await self._get_historical_data_from_db(symbol, timeframe, lookback_days)
                if df is None or df.empty:
                    df = await self._fetch_historical_data_from_binance(symbol, timeframe, lookback_days)
                    if df is not None and not df.empty:
                        await self._store_historical_data_to_db(symbol, timeframe, df)
                
                if df is not None and not df.empty:
                    # Calculate returns
                    df['returns'] = df['close'].pct_change()
                    price_data[symbol] = df['returns'].dropna()
            
            if len(price_data) < 2:
                return {
                    "symbols": symbols,
                    "correlation_matrix": {},
                    "insights": ["Insufficient data for correlation analysis"]
                }
            
            # Create correlation matrix
            returns_df = pd.DataFrame(price_data)
            correlation_matrix = returns_df.corr()
            
            # Find high correlations
            high_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:
                        high_correlations.append({
                            "symbol1": correlation_matrix.columns[i],
                            "symbol2": correlation_matrix.columns[j],
                            "correlation": float(corr_value),
                            "type": "high_positive" if corr_value > 0 else "high_negative"
                        })
            
            # Generate insights
            insights = []
            if high_correlations:
                insights.append(f"Found {len(high_correlations)} high correlations (>0.7)")
                for corr in high_correlations[:3]:  # Top 3
                    insights.append(f"{corr['symbol1']} and {corr['symbol2']}: {corr['correlation']:.3f}")
            
            # Calculate average correlation
            avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
            insights.append(f"Average correlation: {avg_correlation:.3f}")
            
            return {
                "symbols": symbols,
                "correlation_matrix": correlation_matrix.to_dict(),
                "high_correlations": high_correlations,
                "average_correlation": float(avg_correlation),
                "insights": insights,
                "data_points": len(returns_df)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing cross-asset correlations: {e}")
            return {
                "symbols": symbols,
                "correlation_matrix": {},
                "insights": [f"Error: {str(e)}"]
            }
    
    async def detect_market_regimes(self, symbol: str) -> Dict[str, Any]:
        """Detect market regimes."""
        # Placeholder implementation
        return {
            "symbol": symbol,
            "current_regime": "trending",
            "regime_confidence": 0.8
        }
    
    async def generate_ml_strategies(self, symbol: str) -> List[Dict[str, Any]]:
        """Generate machine learning strategies."""
        # Placeholder implementation
        return [{
            "name": f"{symbol}_ml_strategy",
            "type": "machine_learning",
            "model_type": "random_forest",
            "confidence": 0.7
        }]
    
    async def manage_exchange_credentials(self, exchange: str, action: str, credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Manage exchange credentials in Vault."""
        try:
            vault_client = get_vault_client()
            
            if action == "get":
                # Get existing credentials
                creds = vault_client.get_exchange_credentials(exchange)
                if creds:
                    return {
                        "status": "success",
                        "exchange": exchange,
                        "has_credentials": True,
                        "credentials": {k: "***" if k in ["api_key", "secret_key"] else v for k, v in creds.items()}
                    }
                else:
                    return {
                        "status": "success",
                        "exchange": exchange,
                        "has_credentials": False,
                        "credentials": None
                    }
            
            elif action == "set" and credentials:
                # Store new credentials
                success = vault_client.put_secret(f"api_keys/{exchange}", credentials)
                if success:
                    return {
                        "status": "success",
                        "exchange": exchange,
                        "message": f"Credentials for {exchange} updated successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "exchange": exchange,
                        "message": f"Failed to update credentials for {exchange}"
                    }
            
            elif action == "delete":
                # Delete credentials (implement as needed)
                return {
                    "status": "success",
                    "exchange": exchange,
                    "message": f"Delete operation for {exchange} (implement as needed)"
                }
            
            else:
                return {
                    "status": "error",
                    "message": "Invalid action or missing credentials"
                }
                
        except Exception as e:
            logger.error(f"Error managing credentials for {exchange}: {e}")
            return {
                "status": "error",
                "exchange": exchange,
                "message": str(e)
            }
    
    async def list_exchange_credentials(self) -> Dict[str, Any]:
        """List all available exchange credentials."""
        try:
            vault_client = get_vault_client()
            secrets = vault_client.list_secrets("api_keys")
            
            credential_info = []
            for exchange in secrets:
                creds = vault_client.get_exchange_credentials(exchange)
                credential_info.append({
                    "exchange": exchange,
                    "has_credentials": creds is not None,
                    "last_updated": creds.get("updated_at", "unknown") if creds else None
                })
            
            return {
                "status": "success",
                "exchanges": credential_info
            }
            
        except Exception as e:
            logger.error(f"Error listing exchange credentials: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def test_exchange_connection(self, exchange: str) -> Dict[str, Any]:
        """Test connection to an exchange using stored credentials."""
        try:
            credentials = get_exchange_credentials(exchange)
            if not credentials:
                return {
                    "status": "error",
                    "exchange": exchange,
                    "message": f"No credentials found for {exchange}"
                }
            
            # Test connection based on exchange type
            if exchange == "binance":
                # Test with Binance US (authenticated API)
                logger.info("Testing Binance US authenticated API connection")
                test_exchange = ccxt.binanceus({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret_key'),
                    'sandbox': False,
                    'enableRateLimit': True,
                })
            else:
                # Generic test for other exchanges
                exchange_class = getattr(ccxt, exchange, None)
                if not exchange_class:
                    return {
                        "status": "error",
                        "exchange": exchange,
                        "message": f"Unsupported exchange: {exchange}"
                    }
                
                test_exchange = exchange_class({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret_key'),
                    'enableRateLimit': True,
                })
            
            # Test basic API call
            try:
                # Try to fetch ticker for a common symbol
                if exchange == "binance":
                    ticker = test_exchange.fetch_ticker("BTC/USD")
                else:
                    ticker = test_exchange.fetch_ticker("BTC/USDT")
                
                return {
                    "status": "success",
                    "exchange": exchange,
                    "message": "Connection successful",
                    "test_symbol": ticker.get("symbol", "unknown"),
                    "last_price": ticker.get("last", "unknown")
                }
                
            except Exception as api_error:
                return {
                    "status": "warning",
                    "exchange": exchange,
                    "message": f"API test failed: {str(api_error)}",
                    "note": "Credentials may be valid but API call failed"
                }
                
        except Exception as e:
            logger.error(f"Error testing connection to {exchange}: {e}")
            return {
                "status": "error",
                "exchange": exchange,
                "message": str(e)
            }
    
    async def _run_strategy_backtest(self, strategy: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Run backtest simulation for a strategy."""
        try:
            strategy_type = strategy.get("type", "trend_following")
            parameters = strategy.get("parameters", {})
            
            # Initialize backtest variables
            initial_capital = 10000  # $10,000 starting capital
            current_capital = initial_capital
            position = 0  # 0 = no position, 1 = long, -1 = short
            entry_price = 0
            trades = []
            
            # Calculate technical indicators
            df = self._add_technical_indicators(df)
            
            for i in range(20, len(df)):  # Start after enough data for indicators
                current_price = df.iloc[i]['close']
                current_time = df.iloc[i]['time']
                
                # Check entry conditions based on strategy type
                should_enter = self._check_entry_condition(strategy_type, parameters, df, i)
                should_exit = self._check_exit_condition(strategy_type, parameters, df, i)
                
                # Execute trades
                if should_enter and position == 0:
                    # Enter position
                    position = 1  # Long position
                    entry_price = current_price
                    entry_time = current_time
                    
                elif should_exit and position != 0:
                    # Exit position
                    exit_price = current_price
                    pnl = (exit_price - entry_price) * (current_capital / entry_price)
                    current_capital += pnl
                    
                    trades.append({
                        "entry_time": entry_time,
                        "exit_time": current_time,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": pnl,
                        "return_pct": (pnl / (current_capital - pnl)) * 100
                    })
                    
                    position = 0
                    entry_price = 0
            
            # Close any open position at the end
            if position != 0:
                exit_price = df.iloc[-1]['close']
                pnl = (exit_price - entry_price) * (current_capital / entry_price)
                current_capital += pnl
                
                trades.append({
                    "entry_time": entry_time,
                    "exit_time": df.iloc[-1]['time'],
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "return_pct": (pnl / (current_capital - pnl)) * 100
                })
            
            return {
                "initial_capital": initial_capital,
                "final_capital": current_capital,
                "total_return": current_capital - initial_capital,
                "total_return_pct": ((current_capital - initial_capital) / initial_capital) * 100,
                "trades": trades,
                "total_trades": len(trades)
            }
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {
                "error": str(e),
                "trades": [],
                "total_trades": 0
            }
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe."""
        try:
            # Calculate moving averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # Calculate RSI
            df['rsi'] = self._calculate_rsi(df['close'])
            
            # Calculate ATR
            df['atr'] = self._calculate_atr(df)
            
            # Calculate Bollinger Bands
            df['bb_upper'] = df['sma_20'] + (df['close'].rolling(window=20).std() * 2)
            df['bb_lower'] = df['sma_20'] - (df['close'].rolling(window=20).std() * 2)
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            return df
    
    def _check_entry_condition(self, strategy_type: str, parameters: Dict[str, Any], df: pd.DataFrame, index: int) -> bool:
        """Check if entry condition is met."""
        try:
            if strategy_type == "trend_following":
                # Entry: price above 20-day SMA
                return df.iloc[index]['close'] > df.iloc[index]['sma_20']
            
            elif strategy_type == "mean_reversion":
                # Entry: RSI below 30 (oversold) or above 70 (overbought)
                rsi = df.iloc[index]['rsi']
                return rsi < 30 or rsi > 70
            
            elif strategy_type == "breakout":
                # Entry: price breaks above upper Bollinger Band
                return df.iloc[index]['close'] > df.iloc[index]['bb_upper']
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking entry condition: {e}")
            return False
    
    def _check_exit_condition(self, strategy_type: str, parameters: Dict[str, Any], df: pd.DataFrame, index: int) -> bool:
        """Check if exit condition is met."""
        try:
            if strategy_type == "trend_following":
                # Exit: price below 20-day SMA
                return df.iloc[index]['close'] < df.iloc[index]['sma_20']
            
            elif strategy_type == "mean_reversion":
                # Exit: RSI returns to neutral (40-60)
                rsi = df.iloc[index]['rsi']
                return 40 <= rsi <= 60
            
            elif strategy_type == "breakout":
                # Exit: price returns to middle of Bollinger Bands
                return df.iloc[index]['close'] <= df.iloc[index]['sma_20']
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking exit condition: {e}")
            return False
    
    def _calculate_performance_metrics(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        try:
            trades = backtest_results.get("trades", [])
            total_trades = len(trades)
            
            if total_trades == 0:
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "profit_loss": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe_ratio": 0.0,
                    "avg_trade_return": 0.0,
                    "best_trade": 0.0,
                    "worst_trade": 0.0
                }
            
            # Calculate basic metrics
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] <= 0]
            
            win_rate = len(winning_trades) / total_trades * 100
            total_pnl = sum(t['pnl'] for t in trades)
            avg_trade_return = total_pnl / total_trades
            
            # Calculate max drawdown
            capital_curve = [backtest_results['initial_capital']]
            for trade in trades:
                capital_curve.append(capital_curve[-1] + trade['pnl'])
            
            max_drawdown = 0
            peak = capital_curve[0]
            for capital in capital_curve:
                if capital > peak:
                    peak = capital
                drawdown = (peak - capital) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            # Calculate Sharpe ratio (simplified)
            returns = [t['return_pct'] for t in trades]
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            
            return {
                "total_trades": total_trades,
                "win_rate": round(win_rate, 2),
                "profit_loss": round(total_pnl, 2),
                "max_drawdown": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "avg_trade_return": round(avg_trade_return, 2),
                "best_trade": round(max(t['pnl'] for t in trades), 2),
                "worst_trade": round(min(t['pnl'] for t in trades), 2),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades)
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {
                "error": str(e),
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_loss": 0.0,
                "max_drawdown": 0.0
            }
    
    async def _store_sandbox_results(self, sandbox_id: str, strategy: Dict[str, Any], backtest_results: Dict[str, Any], performance_metrics: Dict[str, Any]) -> bool:
        """Store sandbox test results in database."""
        try:
            with get_session() as session:
                # Create sandbox record
                sandbox_record = Backtest(
                    id=sandbox_id,
                    strategy_name=strategy.get("name", "unknown"),
                    symbol=strategy.get("symbol", "unknown"),
                    timeframe=strategy.get("timeframe", "1d"),
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    initial_capital=backtest_results.get("initial_capital", 0),
                    final_capital=backtest_results.get("final_capital", 0),
                    total_return=backtest_results.get("total_return", 0),
                    total_trades=performance_metrics.get("total_trades", 0),
                    win_rate=performance_metrics.get("win_rate", 0),
                    max_drawdown=performance_metrics.get("max_drawdown", 0),
                    sharpe_ratio=performance_metrics.get("sharpe_ratio", 0),
                    status="completed",
                    metadata={
                        "strategy": strategy,
                        "backtest_results": backtest_results,
                        "performance_metrics": performance_metrics
                    }
                )
                
                session.add(sandbox_record)
                session.commit()
                
                logger.info(f"Stored sandbox results for {sandbox_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing sandbox results: {e}")
            return False
    
    async def explain_strategy_results(self, sandbox_results: Dict[str, Any]) -> Dict[str, Any]:
        """Explain strategy results in simple, user-friendly terms."""
        try:
            performance = sandbox_results.get("performance_metrics", {})
            backtest = sandbox_results.get("backtest_results", {})
            strategy = sandbox_results.get("strategy", {})
            
            # Calculate key insights
            total_return_pct = backtest.get("total_return_pct", 0)
            win_rate = performance.get("win_rate", 0)
            max_drawdown = performance.get("max_drawdown", 0)
            total_trades = performance.get("total_trades", 0)
            
            # Generate user-friendly explanations
            explanation = {
                "summary": self._generate_summary(total_return_pct, win_rate, max_drawdown),
                "what_happened": self._explain_what_happened(backtest, strategy),
                "why_it_happened": self._explain_why_it_happened(performance, strategy),
                "risk_assessment": self._assess_risk(max_drawdown, win_rate),
                "recommendation": self._generate_recommendation(total_return_pct, win_rate, max_drawdown),
                "simple_metrics": {
                    "total_return": f"${backtest.get('total_return', 0):,.2f}",
                    "return_percentage": f"{total_return_pct:.1f}%",
                    "win_rate": f"{win_rate:.1f}%",
                    "max_loss": f"{max_drawdown:.1f}%",
                    "number_of_trades": total_trades
                }
            }
            
            return {
                "status": "success",
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Error explaining strategy results: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _generate_summary(self, total_return_pct: float, win_rate: float, max_drawdown: float) -> str:
        """Generate a simple summary of the strategy performance."""
        if total_return_pct > 20:
            performance = "excellent"
        elif total_return_pct > 10:
            performance = "good"
        elif total_return_pct > 0:
            performance = "moderate"
        else:
            performance = "poor"
        
        if win_rate > 60:
            consistency = "very consistent"
        elif win_rate > 40:
            consistency = "moderately consistent"
        else:
            consistency = "inconsistent"
        
        return f"This strategy showed {performance} performance with {consistency} results. " \
               f"It made {total_return_pct:.1f}% profit while never losing more than {max_drawdown:.1f}% at any point."
    
    def _explain_what_happened(self, backtest: Dict[str, Any], strategy: Dict[str, Any]) -> str:
        """Explain what happened during the backtest in simple terms."""
        trades = backtest.get("trades", [])
        strategy_type = strategy.get("type", "unknown")
        symbol = strategy.get("symbol", "unknown")
        
        if not trades:
            return f"The strategy didn't make any trades during the test period."
        
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) <= 0]
        
        explanation = f"The {strategy_type} strategy for {symbol} made {len(trades)} trades over the test period. "
        
        if winning_trades:
            best_trade = max(winning_trades, key=lambda x: x.get("pnl", 0))
            explanation += f"The best trade made ${best_trade.get('pnl', 0):,.2f} profit. "
        
        if losing_trades:
            worst_trade = min(losing_trades, key=lambda x: x.get("pnl", 0))
            explanation += f"The worst trade lost ${abs(worst_trade.get('pnl', 0)):,.2f}. "
        
        return explanation
    
    def _explain_why_it_happened(self, performance: Dict[str, Any], strategy: Dict[str, Any]) -> str:
        """Explain why the strategy performed as it did."""
        strategy_type = strategy.get("type", "unknown")
        win_rate = performance.get("win_rate", 0)
        avg_trade_return = performance.get("avg_trade_return", 0)
        
        if strategy_type == "trend_following":
            explanation = "This strategy follows market trends - it buys when prices are rising and sells when they start falling. "
        elif strategy_type == "mean_reversion":
            explanation = "This strategy bets that prices will return to normal levels after extreme moves - it buys when prices are very low and sells when they're very high. "
        elif strategy_type == "breakout":
            explanation = "This strategy looks for sudden price movements and tries to catch the momentum. "
        else:
            explanation = "This strategy uses a combination of market indicators to make trading decisions. "
        
        if win_rate > 60:
            explanation += "The high win rate suggests the strategy is good at picking the right moments to trade. "
        elif win_rate < 30:
            explanation += "The low win rate suggests the strategy needs improvement in timing trades. "
        else:
            explanation += "The moderate win rate shows mixed results in trade timing. "
        
        if avg_trade_return > 0:
            explanation += "On average, each trade made money, which is a positive sign. "
        else:
            explanation += "On average, each trade lost money, which needs attention. "
        
        return explanation
    
    def _assess_risk(self, max_drawdown: float, win_rate: float) -> str:
        """Assess the risk level of the strategy."""
        if max_drawdown < 5:
            risk_level = "low"
            risk_description = "very safe"
        elif max_drawdown < 15:
            risk_level = "moderate"
            risk_description = "reasonably safe"
        elif max_drawdown < 25:
            risk_level = "high"
            risk_description = "somewhat risky"
        else:
            risk_level = "very high"
            risk_description = "very risky"
        
        if win_rate > 50:
            consistency = "consistent"
        else:
            consistency = "inconsistent"
        
        return f"This strategy has {risk_level} risk ({risk_description}). " \
               f"The maximum loss was {max_drawdown:.1f}%, and it shows {consistency} results. " \
               f"This makes it suitable for {'conservative' if risk_level in ['low', 'moderate'] else 'aggressive'} investors."
    
    def _generate_recommendation(self, total_return_pct: float, win_rate: float, max_drawdown: float) -> str:
        """Generate a recommendation based on performance."""
        if total_return_pct > 15 and win_rate > 50 and max_drawdown < 15:
            return "STRONG BUY: This strategy shows excellent performance with good risk management. Consider using it with real money."
        elif total_return_pct > 10 and win_rate > 40 and max_drawdown < 20:
            return "BUY: This strategy shows good potential with acceptable risk. Consider testing it further before real trading."
        elif total_return_pct > 5 and win_rate > 30:
            return "HOLD: This strategy shows some promise but needs improvement. Consider optimizing the parameters."
        elif total_return_pct > 0:
            return "WATCH: This strategy barely made money. Needs significant improvement before real trading."
        else:
            return "AVOID: This strategy lost money and should not be used for real trading."
    
    async def explain_market_conditions(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Explain current market conditions in simple terms."""
        try:
            patterns = market_data.get("patterns", {})
            trend = patterns.get("price_trend", {})
            volatility = patterns.get("volatility", {})
            
            # Generate market explanation
            trend_direction = trend.get("direction", "unknown")
            trend_strength = trend.get("strength", "unknown")
            volatility_level = volatility.get("level", "unknown")
            
            explanation = {
                "current_market": self._explain_market_trend(trend_direction, trend_strength),
                "volatility": self._explain_volatility(volatility_level),
                "trading_environment": self._explain_trading_environment(trend_direction, volatility_level),
                "simple_insights": {
                    "market_direction": trend_direction.title(),
                    "trend_strength": trend_strength.title(),
                    "volatility": volatility_level.title()
                }
            }
            
            return {
                "status": "success",
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Error explaining market conditions: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _explain_market_trend(self, direction: str, strength: str) -> str:
        """Explain market trend in simple terms."""
        if direction == "uptrend":
            if strength == "strong":
                return "The market is strongly moving upward, which is generally good for buying strategies."
            else:
                return "The market is moving upward, which provides opportunities for growth."
        elif direction == "downtrend":
            if strength == "strong":
                return "The market is strongly moving downward, which requires careful risk management."
            else:
                return "The market is moving downward, which may require defensive strategies."
        else:
            return "The market is moving sideways, which can be challenging for trend-following strategies."
    
    def _explain_volatility(self, level: str) -> str:
        """Explain volatility in simple terms."""
        if level == "high":
            return "High volatility means prices are moving dramatically up and down. This creates both opportunities and risks."
        elif level == "low":
            return "Low volatility means prices are relatively stable. This is safer but may offer fewer trading opportunities."
        else:
            return "Moderate volatility provides a balance of opportunities and manageable risk."
    
    def _explain_trading_environment(self, trend: str, volatility: str) -> str:
        """Explain the overall trading environment."""
        if trend == "uptrend" and volatility == "low":
            return "This is an ideal environment for conservative growth strategies."
        elif trend == "uptrend" and volatility == "high":
            return "This environment offers high potential returns but requires careful risk management."
        elif trend == "downtrend":
            return "This environment requires defensive strategies and capital preservation focus."
        else:
            return "This is a mixed environment that requires adaptable trading strategies."
    
    async def explain_performance_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Explain performance metrics in simple terms."""
        try:
            win_rate = metrics.get("win_rate", 0)
            profit_loss = metrics.get("profit_loss", 0)
            max_drawdown = metrics.get("max_drawdown", 0)
            sharpe_ratio = metrics.get("sharpe_ratio", 0)
            
            explanation = {
                "win_rate_explanation": self._explain_win_rate(win_rate),
                "profit_explanation": self._explain_profit(profit_loss),
                "risk_explanation": self._explain_risk_metrics(max_drawdown, sharpe_ratio),
                "overall_assessment": self._assess_overall_performance(win_rate, profit_loss, max_drawdown),
                "simple_breakdown": {
                    "win_rate": f"{win_rate:.1f}% of trades were profitable",
                    "total_profit": f"${profit_loss:,.2f} total profit/loss",
                    "max_loss": f"{max_drawdown:.1f}% maximum loss at any point",
                    "risk_adjusted": f"{sharpe_ratio:.2f} risk-adjusted return (higher is better)"
                }
            }
            
            return {
                "status": "success",
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Error explaining performance metrics: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _explain_win_rate(self, win_rate: float) -> str:
        """Explain win rate in simple terms."""
        if win_rate > 70:
            return f"Excellent win rate of {win_rate:.1f}% - this strategy is very good at picking winning trades."
        elif win_rate > 50:
            return f"Good win rate of {win_rate:.1f}% - this strategy wins more often than it loses."
        elif win_rate > 30:
            return f"Moderate win rate of {win_rate:.1f}% - this strategy needs improvement in trade selection."
        else:
            return f"Low win rate of {win_rate:.1f}% - this strategy needs significant improvement."
    
    def _explain_profit(self, profit_loss: float) -> str:
        """Explain profit/loss in simple terms."""
        if profit_loss > 1000:
            return f"Strong profit of ${profit_loss:,.2f} - this strategy is making good money."
        elif profit_loss > 0:
            return f"Modest profit of ${profit_loss:,.2f} - this strategy is profitable but could be improved."
        elif profit_loss > -1000:
            return f"Small loss of ${abs(profit_loss):,.2f} - this strategy needs improvement."
        else:
            return f"Significant loss of ${abs(profit_loss):,.2f} - this strategy is not working well."
    
    def _explain_risk_metrics(self, max_drawdown: float, sharpe_ratio: float) -> str:
        """Explain risk metrics in simple terms."""
        risk_explanation = f"The maximum loss at any point was {max_drawdown:.1f}%. "
        
        if max_drawdown < 10:
            risk_explanation += "This is very low risk - the strategy is very safe."
        elif max_drawdown < 20:
            risk_explanation += "This is moderate risk - the strategy is reasonably safe."
        else:
            risk_explanation += "This is high risk - the strategy can have significant losses."
        
        if sharpe_ratio > 1:
            risk_explanation += f" The risk-adjusted return of {sharpe_ratio:.2f} is excellent."
        elif sharpe_ratio > 0.5:
            risk_explanation += f" The risk-adjusted return of {sharpe_ratio:.2f} is good."
        else:
            risk_explanation += f" The risk-adjusted return of {sharpe_ratio:.2f} needs improvement."
        
        return risk_explanation
    
    def _assess_overall_performance(self, win_rate: float, profit_loss: float, max_drawdown: float) -> str:
        """Assess overall performance."""
        if profit_loss > 1000 and win_rate > 50 and max_drawdown < 15:
            return "EXCELLENT: This strategy shows strong performance with good risk management."
        elif profit_loss > 0 and win_rate > 40 and max_drawdown < 20:
            return "GOOD: This strategy is profitable with acceptable risk."
        elif profit_loss > 0:
            return "ACCEPTABLE: This strategy makes money but could be improved."
        else:
            return "POOR: This strategy needs significant improvement before real trading."
    
    async def generate_user_summary(self, sandbox_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive user-friendly summary."""
        try:
            # Get explanations
            strategy_explanation = await self.explain_strategy_results(sandbox_results)
            performance_explanation = await self.explain_performance_metrics(sandbox_results.get("performance_metrics", {}))
            
            # Combine into comprehensive summary
            summary = {
                "quick_overview": strategy_explanation.get("explanation", {}).get("summary", ""),
                "what_happened": strategy_explanation.get("explanation", {}).get("what_happened", ""),
                "why_it_happened": strategy_explanation.get("explanation", {}).get("why_it_happened", ""),
                "risk_level": strategy_explanation.get("explanation", {}).get("risk_assessment", ""),
                "recommendation": strategy_explanation.get("explanation", {}).get("recommendation", ""),
                "performance_breakdown": performance_explanation.get("explanation", {}).get("simple_breakdown", {}),
                "key_metrics": strategy_explanation.get("explanation", {}).get("simple_metrics", {}),
                "next_steps": self._generate_next_steps(sandbox_results)
            }
            
            return {
                "status": "success",
                "user_summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error generating user summary: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _generate_next_steps(self, sandbox_results: Dict[str, Any]) -> str:
        """Generate next steps based on results."""
        performance = sandbox_results.get("performance_metrics", {})
        total_return_pct = sandbox_results.get("backtest_results", {}).get("total_return_pct", 0)
        win_rate = performance.get("win_rate", 0)
        max_drawdown = performance.get("max_drawdown", 0)
        
        if total_return_pct > 15 and win_rate > 50 and max_drawdown < 15:
            return "Consider using this strategy with real money, starting with a small amount to test."
        elif total_return_pct > 10 and win_rate > 40:
            return "Test this strategy further with different market conditions before real trading."
        elif total_return_pct > 0:
            return "Optimize the strategy parameters to improve performance before real trading."
        else:
            return "This strategy needs significant improvement. Consider different approaches or market conditions."
    
    async def evaluate_strategy_for_promotion(self, sandbox_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if a strategy meets promotion criteria to production."""
        try:
            performance = sandbox_results.get("performance_metrics", {})
            backtest = sandbox_results.get("backtest_results", {})
            strategy = sandbox_results.get("strategy", {})
            
            # Define promotion criteria
            promotion_criteria = {
                "min_total_return_pct": 15.0,  # Minimum 15% return
                "min_win_rate": 50.0,          # Minimum 50% win rate
                "max_drawdown": 20.0,          # Maximum 20% drawdown
                "min_trades": 5,               # Minimum 5 trades
                "min_sharpe_ratio": 0.5,       # Minimum Sharpe ratio
                "min_profit": 1000.0           # Minimum $1000 profit
            }
            
            # Extract metrics
            total_return_pct = backtest.get("total_return_pct", 0)
            win_rate = performance.get("win_rate", 0)
            max_drawdown = performance.get("max_drawdown", 0)
            total_trades = performance.get("total_trades", 0)
            sharpe_ratio = performance.get("sharpe_ratio", 0)
            total_profit = backtest.get("total_return", 0)
            
            # Evaluate each criterion
            evaluation = {
                "total_return_pct": {
                    "value": total_return_pct,
                    "required": promotion_criteria["min_total_return_pct"],
                    "passed": total_return_pct >= promotion_criteria["min_total_return_pct"],
                    "weight": 0.25
                },
                "win_rate": {
                    "value": win_rate,
                    "required": promotion_criteria["min_win_rate"],
                    "passed": win_rate >= promotion_criteria["min_win_rate"],
                    "weight": 0.20
                },
                "max_drawdown": {
                    "value": max_drawdown,
                    "required": promotion_criteria["max_drawdown"],
                    "passed": max_drawdown <= promotion_criteria["max_drawdown"],
                    "weight": 0.20
                },
                "total_trades": {
                    "value": total_trades,
                    "required": promotion_criteria["min_trades"],
                    "passed": total_trades >= promotion_criteria["min_trades"],
                    "weight": 0.10
                },
                "sharpe_ratio": {
                    "value": sharpe_ratio,
                    "required": promotion_criteria["min_sharpe_ratio"],
                    "passed": sharpe_ratio >= promotion_criteria["min_sharpe_ratio"],
                    "weight": 0.15
                },
                "total_profit": {
                    "value": total_profit,
                    "required": promotion_criteria["min_profit"],
                    "passed": total_profit >= promotion_criteria["min_profit"],
                    "weight": 0.10
                }
            }
            
            # Calculate overall score
            total_score = 0
            passed_criteria = 0
            
            for criterion, data in evaluation.items():
                if data["passed"]:
                    total_score += data["weight"]
                    passed_criteria += 1
            
            # Determine promotion status
            promotion_threshold = 0.75  # 75% of criteria must pass
            eligible_for_promotion = total_score >= promotion_threshold
            
            # Generate promotion recommendation
            if eligible_for_promotion:
                recommendation = "PROMOTE: Strategy meets promotion criteria and is ready for production trading."
                risk_level = self._assess_production_risk(max_drawdown, win_rate)
            else:
                recommendation = "HOLD: Strategy does not meet promotion criteria. Continue testing and optimization."
                risk_level = "not_applicable"
            
            return {
                "status": "success",
                "eligible_for_promotion": eligible_for_promotion,
                "total_score": round(total_score, 3),
                "passed_criteria": passed_criteria,
                "total_criteria": len(evaluation),
                "promotion_threshold": promotion_threshold,
                "evaluation": evaluation,
                "recommendation": recommendation,
                "risk_level": risk_level,
                "promotion_criteria": promotion_criteria
            }
            
        except Exception as e:
            logger.error(f"Error evaluating strategy for promotion: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _assess_production_risk(self, max_drawdown: float, win_rate: float) -> str:
        """Assess risk level for production trading."""
        if max_drawdown < 10 and win_rate > 60:
            return "low"
        elif max_drawdown < 15 and win_rate > 50:
            return "moderate"
        elif max_drawdown < 20 and win_rate > 40:
            return "high"
        else:
            return "very_high"
    
    async def promote_strategy_to_production(self, sandbox_results: Dict[str, Any], user_approval: bool = False) -> Dict[str, Any]:
        """Promote a strategy from sandbox to production trading."""
        try:
            # First evaluate if strategy is eligible
            evaluation = await self.evaluate_strategy_for_promotion(sandbox_results)
            
            if evaluation["status"] != "success":
                return evaluation
            
            if not evaluation["eligible_for_promotion"]:
                return {
                    "status": "error",
                    "message": "Strategy does not meet promotion criteria",
                    "evaluation": evaluation
                }
            
            # Check if user approval is required and provided
            if not user_approval:
                return {
                    "status": "pending_approval",
                    "message": "User approval required for strategy promotion",
                    "evaluation": evaluation
                }
            
            strategy = sandbox_results.get("strategy", {})
            performance = sandbox_results.get("performance_metrics", {})
            
            # Create production strategy record
            production_strategy = {
                "id": f"prod_{strategy.get('name', 'strategy')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "name": strategy.get("name", "unknown"),
                "type": strategy.get("type", "unknown"),
                "symbol": strategy.get("symbol", "unknown"),
                "timeframe": strategy.get("timeframe", "1d"),
                "parameters": strategy.get("parameters", {}),
                "risk_profile": strategy.get("risk_profile", "balanced"),
                "promotion_date": datetime.now().isoformat(),
                "sandbox_performance": {
                    "total_return_pct": sandbox_results.get("backtest_results", {}).get("total_return_pct", 0),
                    "win_rate": performance.get("win_rate", 0),
                    "max_drawdown": performance.get("max_drawdown", 0),
                    "sharpe_ratio": performance.get("sharpe_ratio", 0),
                    "total_trades": performance.get("total_trades", 0)
                },
                "status": "active",
                "allocation": self._calculate_initial_allocation(performance),
                "risk_limits": self._calculate_risk_limits(performance),
                "monitoring_config": self._create_monitoring_config(performance)
            }
            
            # Store in database
            success = await self._store_production_strategy(production_strategy)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Strategy '{strategy.get('name', 'unknown')}' successfully promoted to production",
                    "production_strategy": production_strategy,
                    "evaluation": evaluation
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to store production strategy"
                }
            
        except Exception as e:
            logger.error(f"Error promoting strategy to production: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _calculate_initial_allocation(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate initial capital allocation based on performance."""
        win_rate = performance.get("win_rate", 0)
        max_drawdown = performance.get("max_drawdown", 0)
        sharpe_ratio = performance.get("sharpe_ratio", 0)
        
        # Base allocation on risk-adjusted performance
        base_allocation = 10000  # $10,000 base
        
        # Adjust based on performance metrics
        if sharpe_ratio > 1.0 and win_rate > 60:
            allocation_multiplier = 1.5  # 50% more allocation
        elif sharpe_ratio > 0.5 and win_rate > 50:
            allocation_multiplier = 1.0  # Standard allocation
        else:
            allocation_multiplier = 0.5  # Reduced allocation
        
        # Reduce allocation if high drawdown
        if max_drawdown > 15:
            allocation_multiplier *= 0.7
        
        return {
            "initial_capital": base_allocation * allocation_multiplier,
            "max_position_size": 0.1,  # 10% max per position
            "allocation_multiplier": allocation_multiplier
        }
    
    def _calculate_risk_limits(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk limits for production trading."""
        max_drawdown = performance.get("max_drawdown", 0)
        
        # Set risk limits based on historical performance
        if max_drawdown < 10:
            daily_loss_limit = 0.02  # 2% daily loss limit
            max_drawdown_limit = 0.15  # 15% max drawdown limit
        elif max_drawdown < 15:
            daily_loss_limit = 0.015  # 1.5% daily loss limit
            max_drawdown_limit = 0.20  # 20% max drawdown limit
        else:
            daily_loss_limit = 0.01  # 1% daily loss limit
            max_drawdown_limit = 0.25  # 25% max drawdown limit
        
        return {
            "daily_loss_limit": daily_loss_limit,
            "max_drawdown_limit": max_drawdown_limit,
            "position_size_limit": 0.1,  # 10% max position size
            "stop_loss_multiplier": 2.0  # 2x ATR for stop loss
        }
    
    def _create_monitoring_config(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """Create monitoring configuration for production strategy."""
        win_rate = performance.get("win_rate", 0)
        total_trades = performance.get("total_trades", 0)
        
        # Set monitoring thresholds based on historical performance
        if win_rate > 60:
            performance_threshold = 0.8  # 80% of historical performance
        else:
            performance_threshold = 0.6  # 60% of historical performance
        
        return {
            "performance_threshold": performance_threshold,
            "monitoring_period": "7d",  # Monitor every 7 days
            "alert_threshold": 0.5,  # Alert if performance drops below 50%
            "deactivation_threshold": 0.3,  # Deactivate if performance drops below 30%
            "min_trades_for_evaluation": max(5, total_trades // 4)  # At least 5 trades or 25% of sandbox trades
        }
    
    async def _store_production_strategy(self, strategy: Dict[str, Any]) -> bool:
        """Store production strategy in database."""
        try:
            with get_session() as session:
                # Create production strategy record
                production_record = ProductionStrategy(
                    id=strategy["id"],
                    name=strategy["name"],
                    type=strategy["type"],
                    symbol=strategy["symbol"],
                    timeframe=strategy["timeframe"],
                    parameters=strategy["parameters"],
                    risk_profile=strategy["risk_profile"],
                    status=strategy["status"],
                    allocation=strategy["allocation"],
                    risk_limits=strategy["risk_limits"],
                    monitoring_config=strategy["monitoring_config"],
                    strategy_metadata={
                        "promotion_date": strategy["promotion_date"],
                        "sandbox_performance": strategy["sandbox_performance"]
                    }
                )
                
                session.add(production_record)
                session.commit()
                
                logger.info(f"Stored production strategy: {strategy['id']}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing production strategy: {e}")
            return False
    
    async def manage_strategy_lifecycle(self, strategy_id: str, action: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage strategy lifecycle (activate, pause, resume, deactivate)."""
        try:
            with get_session() as session:
                strategy = session.query(ProductionStrategy).filter(ProductionStrategy.id == strategy_id).first()
                
                if not strategy:
                    return {
                        "status": "error",
                        "message": f"Strategy {strategy_id} not found"
                    }
                
                if action == "activate":
                    strategy.status = "active"
                    message = f"Strategy {strategy_id} activated"
                elif action == "pause":
                    strategy.status = "paused"
                    message = f"Strategy {strategy_id} paused"
                elif action == "resume":
                    strategy.status = "active"
                    message = f"Strategy {strategy_id} resumed"
                elif action == "deactivate":
                    strategy.status = "inactive"
                    message = f"Strategy {strategy_id} deactivated"
                elif action == "update":
                    if parameters:
                        for key, value in parameters.items():
                            if hasattr(strategy, key):
                                setattr(strategy, key, value)
                    message = f"Strategy {strategy_id} updated"
                else:
                    return {
                        "status": "error",
                        "message": f"Invalid action: {action}"
                    }
                
                session.commit()
                
                return {
                    "status": "success",
                    "message": message,
                    "strategy_id": strategy_id,
                    "new_status": strategy.status
                }
                
        except Exception as e:
            logger.error(f"Error managing strategy lifecycle: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def monitor_strategy_performance(self, strategy_id: str) -> Dict[str, Any]:
        """Monitor production strategy performance and generate alerts."""
        try:
            with get_session() as session:
                strategy = session.query(ProductionStrategy).filter(ProductionStrategy.id == strategy_id).first()
                
                if not strategy:
                    return {
                        "status": "error",
                        "message": f"Strategy {strategy_id} not found"
                    }
                
                # Get recent performance data (mock data for now since we don't have real trades)
                # In a real implementation, this would query actual trade data
                mock_recent_trades = []  # Placeholder for actual trade data
                
                if not mock_recent_trades:
                    return {
                        "status": "warning",
                        "message": f"No recent trades found for strategy {strategy_id}",
                        "strategy_id": strategy_id,
                        "note": "This is expected for newly promoted strategies"
                    }
                
                # Calculate current performance metrics
                current_performance = self._calculate_current_performance(mock_recent_trades)
                sandbox_performance = strategy.strategy_metadata.get("sandbox_performance", {})
                
                # Compare with sandbox performance
                performance_ratio = self._calculate_performance_ratio(current_performance, sandbox_performance)
                
                # Generate monitoring report
                monitoring_config = strategy.monitoring_config
                alert_threshold = monitoring_config.get("alert_threshold", 0.5)
                deactivation_threshold = monitoring_config.get("deactivation_threshold", 0.3)
                
                alerts = []
                if performance_ratio < deactivation_threshold:
                    alerts.append("CRITICAL: Performance below deactivation threshold")
                elif performance_ratio < alert_threshold:
                    alerts.append("WARNING: Performance below alert threshold")
                
                return {
                    "status": "success",
                    "strategy_id": strategy_id,
                    "current_performance": current_performance,
                    "sandbox_performance": sandbox_performance,
                    "performance_ratio": performance_ratio,
                    "alerts": alerts,
                    "recommendation": self._generate_monitoring_recommendation(performance_ratio, alerts)
                }
                
        except Exception as e:
            logger.error(f"Error monitoring strategy performance: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _calculate_current_performance(self, trades: List[Any]) -> Dict[str, Any]:
        """Calculate current performance metrics from recent trades."""
        if not trades:
            return {}
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        total_pnl = sum(t.pnl for t in trades)
        avg_trade_return = total_pnl / total_trades if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_trade_return": avg_trade_return,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades)
        }
    
    def _calculate_performance_ratio(self, current: Dict[str, Any], sandbox: Dict[str, Any]) -> float:
        """Calculate performance ratio compared to sandbox results."""
        if not sandbox or not current:
            return 0.0
        
        # Compare win rates
        sandbox_win_rate = sandbox.get("win_rate", 0)
        current_win_rate = current.get("win_rate", 0)
        
        if sandbox_win_rate == 0:
            return 0.0
        
        win_rate_ratio = current_win_rate / sandbox_win_rate
        
        # Compare profitability (simplified)
        sandbox_return = sandbox.get("total_return_pct", 0)
        current_return = current.get("total_pnl", 0) / 10000 * 100  # Assume $10k base
        
        if sandbox_return == 0:
            return win_rate_ratio
        
        return_ratio = current_return / sandbox_return if sandbox_return != 0 else 0
        
        # Weighted average
        return (win_rate_ratio * 0.6) + (return_ratio * 0.4)
    
    def _generate_monitoring_recommendation(self, performance_ratio: float, alerts: List[str]) -> str:
        """Generate recommendation based on monitoring results."""
        if performance_ratio < 0.3:
            return "DEACTIVATE: Strategy performance is critically poor. Consider deactivation."
        elif performance_ratio < 0.5:
            return "PAUSE: Strategy performance is below expectations. Consider pausing for review."
        elif performance_ratio < 0.8:
            return "MONITOR: Strategy performance is below sandbox levels. Continue monitoring closely."
        else:
            return "CONTINUE: Strategy performance is meeting expectations. Continue normal operation."
    
    async def deactivate_strategy(self, strategy_id: str, reason: str = "Performance below threshold") -> Dict[str, Any]:
        """Deactivate a production strategy."""
        try:
            # First pause the strategy
            pause_result = await self.manage_strategy_lifecycle(strategy_id, "pause")
            
            if pause_result["status"] != "success":
                return pause_result
            
            # Update strategy with deactivation reason
            deactivation_data = {
                "status": "deactivated",
                "deactivation_date": datetime.now().isoformat(),
                "deactivation_reason": reason
            }
            
            update_result = await self.manage_strategy_lifecycle(strategy_id, "update", deactivation_data)
            
            return {
                "status": "success",
                "message": f"Strategy {strategy_id} deactivated: {reason}",
                "strategy_id": strategy_id,
                "deactivation_date": deactivation_data["deactivation_date"]
            }
            
        except Exception as e:
            logger.error(f"Error deactivating strategy: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

class AgenticStrategyDiscoveryAgent(BaseAgent):
    """Strategy Discovery Agent for AI-powered strategy discovery."""
    
    def __init__(self):
        # Create LLM config with proper initialization
        llm_config = {
            "config_list": [{"model": "gpt-4o-mini", "api_key": "dummy"}],  # Will be overridden during initialization
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # Create agent config
        config = AgentConfig(
            name="StrategyDiscoveryAgent",
            system_message=self._get_system_message(),
            llm_config=llm_config
        )
        
        super().__init__(config)
        self.tools = StrategyDiscoveryTools()
        self.port = 8025
        
        # Initialize infrastructure clients
        self.db_client = None
        self.vault_client = None
        self.ws_client = None
        
        # Initialize with proper OpenAI configuration
        self._initialize_openai_config()
        
        # Initialize infrastructure connections
        self._initialize_infrastructure()
    
    def _initialize_infrastructure(self):
        """Initialize infrastructure connections (database, vault, websocket)."""
        try:
            # Initialize database client
            from common.db import get_db_client
            self.db_client = get_db_client()
            logger.info("Database client initialized")
            
            # Initialize vault client
            from common.vault import get_vault_client
            self.vault_client = get_vault_client()
            logger.info("Vault client initialized")
            
            # Initialize websocket client
            from common.websocket_client import AgentWebSocketClient
            self.ws_client = AgentWebSocketClient(
                agent_name="strategy_discovery"
            )
            # Initially disable auto-reconnect to prevent flooding
            self.ws_client.auto_reconnect = False
            logger.info("WebSocket client initialized (auto-reconnect disabled)")
            
            # Don't attempt to connect immediately - let the agent decide when to connect
            
        except Exception as e:
            logger.error(f"Error initializing infrastructure: {e}")
    
    async def _connect_websocket(self):
        """Connect to websocket server."""
        try:
            if self.ws_client:
                # Try to connect with a timeout
                connection_success = await asyncio.wait_for(
                    self.ws_client.connect(), 
                    timeout=10.0
                )
                
                if connection_success:
                    logger.info("WebSocket connected successfully")
                else:
                    logger.warning("WebSocket connection failed - Meta Agent may be at connection limit")
                    # Disable auto-reconnect to prevent flooding
                    self.ws_client.auto_reconnect = False
                    
        except asyncio.TimeoutError:
            logger.warning("WebSocket connection timed out - Meta Agent may be at connection limit")
            if self.ws_client:
                self.ws_client.auto_reconnect = False
        except Exception as e:
            logger.error(f"Error connecting to websocket: {e}")
            if self.ws_client:
                self.ws_client.auto_reconnect = False

    def _initialize_openai_config(self):
        """Initialize OpenAI configuration from Vault."""
        try:
            from common.vault import get_vault_client
            vault_client = get_vault_client()
            
            if vault_client:
                openai_secret = vault_client.get_secret("openai/api_key")
                if openai_secret and "api_key" in openai_secret:
                    openai_api_key = openai_secret["api_key"]
                    # Update the LLM config with the real API key
                    self.config.llm_config = {
                        "config_list": [{
                            "api_type": "openai",
                            "model": "gpt-4o-mini",
                            "api_key": openai_api_key
                        }],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                    logger.info("Strategy Discovery Agent LLM configured with Vault API key")
                else:
                    logger.warning("OpenAI API key not found in Vault")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI config: {e}")
    
    def _get_system_message(self) -> str:
        """Get the system message for the Strategy Discovery Agent."""
        return """You are the Strategy Discovery Agent for VolexSwarm, an AI-powered trading system.

Your primary responsibilities:
1. Analyze market patterns across multiple assets and timeframes
2. Generate trading strategy candidates using AI and machine learning
3. Detect risk profiles (aggressive, conservative, balanced) for strategies
4. Rank strategies based on performance, risk, and consistency
5. Create sandbox testing environments for strategy validation
6. Optimize strategy parameters for maximum performance
7. Analyze cross-asset correlations and market regimes
8. Generate machine learning-based trading strategies

Key capabilities:
- Multi-asset pattern recognition and analysis
- AI-powered strategy generation using various algorithms
- Risk profile detection and classification
- Strategy performance ranking and optimization
- Sandbox testing environment creation
- Cross-asset correlation analysis
- Market regime detection
- Machine learning strategy generation

Always provide detailed analysis and recommendations with confidence scores.
Focus on finding profitable trading opportunities while managing risk appropriately."""

    async def discover_strategies(self, symbols: List[str], risk_profile: str = "balanced") -> Dict[str, Any]:
        """Discover trading strategies for given symbols."""
        try:
            logger.info(f"Starting strategy discovery for symbols: {symbols}")
            
            all_strategies = []
            
            for symbol in symbols:
                # Analyze market patterns
                patterns = await self.tools.analyze_market_patterns(symbol)
                
                # Generate strategy candidates
                candidates = await self.tools.generate_strategy_candidates(symbol, risk_profile)
                
                # Detect risk profiles
                for candidate in candidates:
                    if "error" not in candidate:
                        risk_profile_detected = await self.tools.detect_risk_profile(candidate)
                        candidate["detected_risk_profile"] = risk_profile_detected
                
                all_strategies.extend(candidates)
            
            # Rank strategies
            ranked_strategies = await self.tools.rank_strategies(all_strategies)
            
            return {
                "status": "success",
                "symbols_analyzed": symbols,
                "strategies_found": len(ranked_strategies),
                "strategies": ranked_strategies,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in strategy discovery: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def create_sandbox_test(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive sandbox test for a strategy."""
        try:
            sandbox_id = f"sandbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            symbol = strategy.get("symbol", "BTC/USD")
            timeframe = strategy.get("timeframe", "1d")
            lookback_days = strategy.get("lookback_days", 365)
            
            logger.info(f"Creating sandbox test {sandbox_id} for {symbol}")
            
            # Get historical data for backtesting
            df = await self.tools._get_historical_data_from_db(symbol, timeframe, lookback_days)
            if df is None or df.empty:
                df = await self.tools._fetch_historical_data_from_binance(symbol, timeframe, lookback_days)
                if df is not None and not df.empty:
                    await self.tools._store_historical_data_to_db(symbol, timeframe, df)
            
            if df is None or df.empty:
                return {
                    "status": "error",
                    "message": f"No data available for {symbol}"
                }
            
            # Run backtest simulation
            backtest_results = await self.tools._run_strategy_backtest(strategy, df)
            
            # Calculate performance metrics
            performance_metrics = self.tools._calculate_performance_metrics(backtest_results)
            
            # Store sandbox results in database
            sandbox_record = await self.tools._store_sandbox_results(sandbox_id, strategy, backtest_results, performance_metrics)
            
            # Generate user-friendly explanations
            sandbox_results = {
                "sandbox_id": sandbox_id,
                "strategy": strategy,
                "backtest_results": backtest_results,
                "performance_metrics": performance_metrics,
                "data_points": len(df),
                "test_period": {
                    "start": df['time'].min().isoformat(),
                    "end": df['time'].max().isoformat()
                }
            }
            
            user_explanation = await self.tools.generate_user_summary(sandbox_results)
            
            return {
                "status": "success",
                "sandbox_id": sandbox_id,
                "strategy": strategy,
                "backtest_results": backtest_results,
                "performance_metrics": performance_metrics,
                "data_points": len(df),
                "test_period": {
                    "start": df['time'].min().isoformat(),
                    "end": df['time'].max().isoformat()
                },
                "user_explanation": user_explanation.get("user_summary", {})
            }
            
        except Exception as e:
            logger.error(f"Error creating sandbox test: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

# FastAPI endpoints
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
from typing import List

app = FastAPI(title="Strategy Discovery Agent", version="1.0.0")



class StrategyDiscoveryRequest(BaseModel):
    symbols: List[str]
    risk_profile: str = "balanced"

class SandboxTestRequest(BaseModel):
    strategy: Dict[str, Any]

class CorrelationAnalysisRequest(BaseModel):
    symbols: List[str]
    timeframe: str = "1d"
    lookback_days: int = 90

class CredentialManagementRequest(BaseModel):
    exchange: str
    action: str  # "get", "set", "delete", "test"
    credentials: Optional[Dict[str, str]] = None

class SandboxTestRequest(BaseModel):
    strategy: Dict[str, Any]
    initial_capital: float = 10000
    test_period_days: int = 365
    commission: float = 0.001
    slippage: float = 0.0005

class ExplanationRequest(BaseModel):
    sandbox_results: Dict[str, Any]

class MarketExplanationRequest(BaseModel):
    market_data: Dict[str, Any]

class PerformanceExplanationRequest(BaseModel):
    performance_metrics: Dict[str, Any]

class StrategyPromotionRequest(BaseModel):
    sandbox_results: Dict[str, Any]
    user_approval: bool = False

class StrategyLifecycleRequest(BaseModel):
    strategy_id: str
    action: str  # "activate", "pause", "resume", "deactivate", "update"
    parameters: Optional[Dict[str, Any]] = None

class StrategyMonitoringRequest(BaseModel):
    strategy_id: str

class StrategyDeactivationRequest(BaseModel):
    strategy_id: str
    reason: str = "Performance below threshold"

@app.post("/discover_strategies")
async def discover_strategies(request: StrategyDiscoveryRequest):
    """Discover trading strategies for given symbols."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.discover_strategies(request.symbols, request.risk_profile)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.post("/create_sandbox_test")
async def create_sandbox_test(request: SandboxTestRequest):
    """Create a sandbox test for a strategy."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.create_sandbox_test(request.strategy)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.post("/run_sandbox_test")
async def run_sandbox_test(request: SandboxTestRequest):
    """Run a comprehensive sandbox test with custom parameters."""
    agent = AgenticStrategyDiscoveryAgent()
    
    # Update strategy with custom parameters
    strategy = request.strategy.copy()
    strategy.update({
        "initial_capital": request.initial_capital,
        "test_period_days": request.test_period_days,
        "commission": request.commission,
        "slippage": request.slippage
    })
    
    result = await agent.create_sandbox_test(strategy)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("error", result.get("message", "Unknown error")))
    
    return result

@app.post("/analyze_correlations")
async def analyze_correlations(request: CorrelationAnalysisRequest):
    """Analyze cross-asset correlations."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.analyze_cross_asset_correlations(
        request.symbols, 
        request.timeframe, 
        request.lookback_days
    )
    
    return result

@app.post("/credentials/manage")
async def manage_credentials(request: CredentialManagementRequest):
    """Manage exchange credentials."""
    agent = AgenticStrategyDiscoveryAgent()
    
    if request.action == "test":
        result = await agent.tools.test_exchange_connection(request.exchange)
    else:
        result = await agent.tools.manage_exchange_credentials(
            request.exchange, 
            request.action, 
            request.credentials
        )
    
    return result

@app.get("/credentials/list")
async def list_credentials():
    """List all available exchange credentials."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.list_exchange_credentials()
    return result

@app.post("/explain/strategy_results")
async def explain_strategy_results(request: ExplanationRequest):
    """Explain strategy results in user-friendly terms."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.explain_strategy_results(request.sandbox_results)
    return result

@app.post("/explain/market_conditions")
async def explain_market_conditions(request: MarketExplanationRequest):
    """Explain market conditions in user-friendly terms."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.explain_market_conditions(request.market_data)
    return result

@app.post("/explain/performance_metrics")
async def explain_performance_metrics(request: PerformanceExplanationRequest):
    """Explain performance metrics in user-friendly terms."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.explain_performance_metrics(request.performance_metrics)
    return result

@app.post("/explain/user_summary")
async def generate_user_summary(request: ExplanationRequest):
    """Generate comprehensive user-friendly summary."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.generate_user_summary(request.sandbox_results)
    return result

@app.post("/strategy/evaluate_promotion")
async def evaluate_strategy_promotion(request: ExplanationRequest):
    """Evaluate if a strategy meets promotion criteria."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.evaluate_strategy_for_promotion(request.sandbox_results)
    return result

@app.post("/strategy/promote")
async def promote_strategy(request: StrategyPromotionRequest):
    """Promote a strategy from sandbox to production."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.promote_strategy_to_production(request.sandbox_results, request.user_approval)
    return result

@app.post("/strategy/lifecycle")
async def manage_strategy_lifecycle(request: StrategyLifecycleRequest):
    """Manage strategy lifecycle (activate, pause, resume, deactivate)."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.manage_strategy_lifecycle(request.strategy_id, request.action, request.parameters)
    return result

@app.post("/strategy/monitor")
async def monitor_strategy(request: StrategyMonitoringRequest):
    """Monitor production strategy performance."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.monitor_strategy_performance(request.strategy_id)
    return result

@app.post("/strategy/deactivate")
async def deactivate_strategy(request: StrategyDeactivationRequest):
    """Deactivate a production strategy."""
    agent = AgenticStrategyDiscoveryAgent()
    result = await agent.tools.deactivate_strategy(request.strategy_id, request.reason)
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Create agent instance to check connectivity
        agent = AgenticStrategyDiscoveryAgent()
        
        # Check infrastructure connectivity
        connectivity = {}
        
        # Check database connectivity
        try:
            if hasattr(agent, 'db_client') and agent.db_client:
                connectivity["database"] = {"status": "connected"}
            else:
                connectivity["database"] = {"status": "disconnected"}
        except Exception as e:
            connectivity["database"] = {"status": "error", "error": str(e)}
        
        # Check vault connectivity
        try:
            if hasattr(agent, 'vault_client') and agent.vault_client:
                connectivity["vault"] = {"status": "connected"}
            else:
                connectivity["vault"] = {"status": "disconnected"}
        except Exception as e:
            connectivity["vault"] = {"status": "error", "error": str(e)}
        
        # Check websocket connectivity
        try:
            if hasattr(agent, 'ws_client') and agent.ws_client and agent.ws_client.connected:
                connectivity["websocket"] = {"status": "connected"}
            else:
                connectivity["websocket"] = {"status": "disconnected"}
        except Exception as e:
            connectivity["websocket"] = {"status": "error", "error": str(e)}
        
        return {
            "status": "healthy",
            "agent": "StrategyDiscoveryAgent",
            "timestamp": datetime.now().isoformat(),
            "connectivity": connectivity
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "StrategyDiscoveryAgent",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8025) 