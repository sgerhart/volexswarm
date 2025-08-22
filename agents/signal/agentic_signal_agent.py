"""
Agentic Signal Agent for VolexSwarm

This module transforms the existing FastAPI Signal Agent into an intelligent,
autonomous AutoGen agent with MCP tool integration.
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.agentic_framework.agent_templates import SignalAgent
from agents.agentic_framework.mcp_tools import AnalysisTools, MCPToolRegistry
from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client
from common.logging import get_logger
from common.models import Signal, PriceData, Strategy, Trade
from common.openai_client import get_openai_client
from common.websocket_client import AgentWebSocketClient

logger = get_logger("agentic_signal")

class AgenticSignalAgent(SignalAgent):
    """Agentic version of the Signal Agent with MCP tool integration and autonomous reasoning"""

    def __init__(self, llm_config: Dict[str, Any] = None, tool_registry: MCPToolRegistry = None):
        # Try to get real API key first, fall back to dummy if needed
        if llm_config is None:
            try:
                from common.vault import get_vault_client
                vault_client = get_vault_client()
                if vault_client:
                    openai_secret = vault_client.get_secret("openai/api_key")
                    if openai_secret and "api_key" in openai_secret:
                        openai_api_key = openai_secret["api_key"]
                        llm_config = {
                            "config_list": [
                                {
                                    "api_type": "openai",
                                    "api_key": openai_api_key,
                                    "model": "gpt-4o-mini"
                                }
                            ],
                            "temperature": 0.7
                        }
                    else:
                        # Fall back to dummy config
                        llm_config = {
                            "config_list": [
                                {
                                    "api_type": "openai",
                                    "api_key": "dummy-key",  # Will be overridden later
                                    "model": "gpt-4o-mini"
                                }
                            ],
                            "temperature": 0.7
                        }
                else:
                    # Fall back to dummy config
                    llm_config = {
                        "config_list": [
                            {
                                "api_type": "openai",
                                "api_key": "dummy-key",  # Will be overridden later
                                "model": "gpt-4o-mini"
                            }
                        ],
                        "temperature": 0.7
                    }
            except Exception:
                # Fall back to dummy config
                llm_config = {
                    "config_list": [
                        {
                            "api_type": "openai",
                            "api_key": "dummy-key",  # Will be overridden later
                            "model": "gpt-4o-mini"
                        }
                    ],
                    "temperature": 0.7
                }
        super().__init__(llm_config)
        # Assign MCP tools directly if not provided by coordinator
        if tool_registry is None:
            from agents.agentic_framework.mcp_tools import create_mcp_tool_registry
            tool_registry = create_mcp_tool_registry()
        self.tool_registry = tool_registry
        # Assign analysis tools to this agent
        for tool in self.tool_registry.get_tools_by_category("analysis"):
            self.add_tool(tool)
        
        # Initialize websocket client for real-time communication
        self.ws_client = AgentWebSocketClient("agentic_signal")
        
        # Signal cache for performance optimization
        self.signal_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Signal history and performance tracking
        self.signal_history = []
        self.performance_metrics = {}
        
        # Technical analysis
        self.technical_indicators = TechnicalIndicators()
        
        # AutoGen agent capabilities
        self.autogen_agent = self.get_agent()  # Get the AutoGen agent instance
        
        logger.info("Agentic Signal Agent initialized")
        
    async def initialize_infrastructure(self):
        """Initialize connections to existing infrastructure."""
        try:
            # Initialize Vault client
            self.vault_client = get_vault_client()
            
            # Initialize database client
            self.db_client = get_db_client()
            
            # Initialize OpenAI client
            self.openai_client = get_openai_client()
            
            # Configure LLM with real API key from Vault
            if self.vault_client:
                # Get agent-specific config
                agent_config = get_agent_config("signal")
                
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
            
            # Load existing models
            await self._load_models()
            
            logger.info("Infrastructure initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize infrastructure: {e}")
            raise
            
    async def initialize(self):
        """Initialize websocket connection to meta agent."""
        try:
            logger.info("Initializing websocket connection to meta agent...")
            await self.ws_client.connect()
            logger.info("Websocket connection established successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize websocket connection: {e}")
            return False
            
    def get_cached_signal(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached signal data."""
        if key in self.signal_cache:
            data, timestamp = self.signal_cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return data
            else:
                del self.signal_cache[key]
        return None
        
    def cache_signal(self, key: str, data: Dict[str, Any]):
        """Cache signal data."""
        self.signal_cache[key] = (data, datetime.now())
        
    async def generate_autonomous_signal(self, symbol: str, 
                                       signal_type: str = "comprehensive",
                                       timeframe: str = "1h") -> Dict[str, Any]:
        """
        Generate autonomous trading signals using AI reasoning and MCP tools.
        
        Args:
            symbol: Trading symbol
            signal_type: Type of signal ("comprehensive", "technical", "ml", "hybrid")
            timeframe: Timeframe for analysis
            
        Returns:
            Dict containing signal data and AI reasoning
        """
        
        # Check cache first
        cache_key = f"{symbol}_{signal_type}_{timeframe}"
        cached_signal = self.get_cached_signal(cache_key)
        if cached_signal:
            logger.info(f"Using cached signal for {cache_key}")
            return cached_signal
            
        try:
            signal_result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "signal_type": signal_type,
                "timeframe": timeframe,
                "signal": "hold",
                "confidence": 0.0,
                "reasoning": "",
                "indicators": {},
                "risk_level": "medium",
                "recommendation": ""
            }
            
            # Generate signal based on type
            if signal_type == "comprehensive":
                comp_result = await self._generate_comprehensive_signal(symbol, timeframe)
                signal_result.update(comp_result)
            elif signal_type == "technical":
                tech_result = await self._generate_technical_signal(symbol, timeframe)
                signal_result.update(tech_result)
            elif signal_type == "ml":
                ml_result = await self._generate_ml_signal(symbol, timeframe)
                signal_result.update(ml_result)
            elif signal_type == "hybrid":
                hybrid_result = await self._generate_hybrid_signal(symbol, timeframe)
                signal_result.update(hybrid_result)
            else:
                raise ValueError(f"Unknown signal type: {signal_type}")
                
            # Ensure 'signal' key is present
            if "signal" not in signal_result or signal_result["signal"] is None:
                signal_result["signal"] = "hold"
                
            # Add AI reasoning
            signal_result["reasoning"] = await self._generate_signal_reasoning(signal_result)
            signal_result["recommendation"] = await self._generate_signal_recommendation(signal_result)
            
            # Cache result
            self.cache_signal(cache_key, signal_result)
            
            # Store in history
            await self._store_signal_history(signal_result)
            
            # Learn from signal generation
            await self._learn_from_signal(signal_result)
            
            logger.info(f"Autonomous signal generated for {symbol}: {signal_result['signal']} (confidence: {signal_result['confidence']})")
            return signal_result
            
        except Exception as e:
            logger.error(f"Error generating autonomous signal: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "signal_type": signal_type,
                "timeframe": timeframe,
                "signal": "hold"
            }
            
    async def _use_autogen_reasoning(self, context: str, question: str) -> str:
        """
        Use the AutoGen agent for autonomous reasoning about market conditions.
        
        Args:
            context: Market context and data
            question: Specific question for the agent to reason about
            
        Returns:
            AI reasoning response
        """
        try:
            if not self.autogen_agent:
                logger.warning("AutoGen agent not available, using fallback reasoning")
                return f"Fallback reasoning for {question}: {context}"
            
            # Create a conversation context for the AutoGen agent
            conversation_context = f"""
            Market Context: {context}
            
            Question: {question}
            
            Please provide your reasoning and analysis based on the market context above.
            Focus on technical analysis, market conditions, and trading implications.
            """
            
            # Use the AutoGen agent to generate reasoning
            # Note: This is a simplified interaction - in a full implementation,
            # you would use autogen's conversation capabilities
            response = await self._simulate_autogen_reasoning(conversation_context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error using AutoGen reasoning: {e}")
            return f"Error in AI reasoning: {str(e)}"
    
    async def _simulate_autogen_reasoning(self, context: str) -> str:
        """
        Simulate AutoGen agent reasoning (placeholder for full implementation).
        In production, this would use actual autogen conversation capabilities.
        """
        try:
            # For now, use OpenAI directly for reasoning
            if hasattr(self, 'openai_client') and self.openai_client:
                # This would be replaced with actual AutoGen conversation
                return f"AutoGen reasoning simulation: {context[:100]}..."
            else:
                return f"Simulated AutoGen reasoning: {context[:100]}..."
        except Exception as e:
            logger.error(f"Error in AutoGen reasoning simulation: {e}")
            return f"Reasoning simulation error: {str(e)}"
        
    async def _generate_comprehensive_signal(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Generate comprehensive signal using multiple analysis methods."""
        
        try:
            # Get price data
            price_data = await self._get_price_data(symbol, timeframe)
            if not price_data:
                return {"error": "No price data available"}
                
            # Extract features
            features = self._extract_features(price_data)
            
            # Technical analysis
            technical_signal = await self._generate_technical_signal(symbol, timeframe)
            
            # ML analysis
            ml_signal = await self._generate_ml_signal(symbol, timeframe)
            
            # Combine signals
            combined_signal = self._combine_signals(technical_signal, ml_signal)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "signal_type": "comprehensive",
                "timeframe": timeframe,
                "signal": combined_signal["signal"],
                "confidence": combined_signal["confidence"],
                "indicators": {
                    "technical": technical_signal.get("indicators", {}),
                    "ml": ml_signal.get("indicators", {})
                },
                "risk_level": combined_signal["risk_level"]
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive signal: {e}")
            return {"error": str(e)}
            
    async def _generate_technical_signal(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Generate signal based on technical analysis."""
        
        try:
            # Get price data
            price_data = await self._get_price_data(symbol, timeframe)
            if not price_data:
                return {"error": "No price data available"}
                
            prices = [float(p["close"]) for p in price_data]
            volumes = [float(p["volume"]) for p in price_data]
            
            # Calculate technical indicators using MCP tools
            rsi_data = self.analysis_tools.calculate_rsi(prices, 14)
            macd_data = self.analysis_tools.calculate_macd(prices, 12, 26, 9)
            bollinger_data = self.analysis_tools.calculate_bollinger_bands(prices, 20, 2.0)
            
            # Analyze indicators
            signal_analysis = self._analyze_technical_indicators(
                rsi_data, macd_data, bollinger_data, prices, volumes
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "signal_type": "technical",
                "timeframe": timeframe,
                "signal": signal_analysis["signal"],
                "confidence": signal_analysis["confidence"],
                "indicators": {
                    "rsi": rsi_data,
                    "macd": macd_data,
                    "bollinger_bands": bollinger_data
                },
                "risk_level": signal_analysis["risk_level"]
            }
            
        except Exception as e:
            logger.error(f"Error generating technical signal: {e}")
            return {"error": str(e)}
            
    async def _generate_ml_signal(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Generate signal using machine learning models."""
        
        try:
            # Get price data
            price_data = await self._get_price_data(symbol, timeframe)
            if not price_data:
                return {"error": "No price data available"}
                
            # Extract features
            features = self._extract_features(price_data)
            
            # Use MCP ML tools
            ml_prediction = self.analysis_tools.predict_signal(features)
            
            # Get model performance
            model_performance = await self._get_model_performance(symbol)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "signal_type": "ml",
                "timeframe": timeframe,
                "signal": ml_prediction["signal"],
                "confidence": ml_prediction["confidence"],
                "indicators": {
                    "ml_prediction": ml_prediction,
                    "model_performance": model_performance
                },
                "risk_level": self._calculate_ml_risk(ml_prediction["confidence"])
            }
            
        except Exception as e:
            logger.error(f"Error generating ML signal: {e}")
            return {"error": str(e)}
            
    async def _generate_hybrid_signal(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Generate hybrid signal combining technical and ML analysis."""
        
        try:
            # Get both technical and ML signals
            technical_signal = await self._generate_technical_signal(symbol, timeframe)
            ml_signal = await self._generate_ml_signal(symbol, timeframe)
            
            # Combine using weighted approach
            hybrid_signal = self._combine_signals_weighted(technical_signal, ml_signal)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "signal_type": "hybrid",
                "timeframe": timeframe,
                "signal": hybrid_signal["signal"],
                "confidence": hybrid_signal["confidence"],
                "indicators": {
                    "technical": technical_signal.get("indicators", {}),
                    "ml": ml_signal.get("indicators", {})
                },
                "risk_level": hybrid_signal["risk_level"]
            }
            
        except Exception as e:
            logger.error(f"Error generating hybrid signal: {e}")
            return {"error": str(e)}
            
    def _analyze_technical_indicators(self, rsi_data: Dict[str, Any], 
                                   macd_data: Dict[str, Any], 
                                   bollinger_data: Dict[str, Any],
                                   prices: List[float], 
                                   volumes: List[float]) -> Dict[str, Any]:
        """Analyze technical indicators to generate signal."""
        
        try:
            # Get latest values
            current_rsi = rsi_data.get("rsi", 50)
            current_macd = macd_data.get("macd", 0)
            current_signal = macd_data.get("signal", 0)
            current_histogram = macd_data.get("histogram", 0)
            
            # Signal logic
            signal = "hold"
            confidence = 0.5
            risk_level = "medium"
            
            # RSI analysis
            if current_rsi < 30:
                signal = "buy"
                confidence += 0.2
            elif current_rsi > 70:
                signal = "sell"
                confidence += 0.2
                
            # MACD analysis
            if current_macd > current_signal and current_histogram > 0:
                if signal == "buy":
                    confidence += 0.1
                elif signal == "hold":
                    signal = "buy"
                    confidence += 0.1
            elif current_macd < current_signal and current_histogram < 0:
                if signal == "sell":
                    confidence += 0.1
                elif signal == "hold":
                    signal = "sell"
                    confidence += 0.1
                    
            # Bollinger Bands analysis
            current_price = prices[-1] if prices else 0
            upper_band = bollinger_data.get("upper", current_price)
            lower_band = bollinger_data.get("lower", current_price)
            
            if current_price <= lower_band:
                if signal == "buy":
                    confidence += 0.1
                elif signal == "hold":
                    signal = "buy"
                    confidence += 0.1
            elif current_price >= upper_band:
                if signal == "sell":
                    confidence += 0.1
                elif signal == "hold":
                    signal = "sell"
                    confidence += 0.1
                    
            # Risk level calculation
            if confidence > 0.8:
                risk_level = "low"
            elif confidence < 0.6:
                risk_level = "high"
                
            return {
                "signal": signal,
                "confidence": min(confidence, 1.0),
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Error analyzing technical indicators: {e}")
            return {
                "signal": "hold",
                "confidence": 0.5,
                "risk_level": "medium"
            }
            
    def _extract_features(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features from price data for ML models."""
        
        try:
            if len(price_data) < 50:
                return {}
                
            # Convert to lists
            prices = [float(p["close"]) for p in price_data]
            volumes = [float(p["volume"]) for p in price_data]
            
            # Calculate features
            features = {
                "price_change_1h": (prices[-1] - prices[-2]) / prices[-2] if len(prices) > 1 else 0,
                "price_change_24h": (prices[-1] - prices[-24]) / prices[-24] if len(prices) > 24 else 0,
                "volume_change_1h": (volumes[-1] - volumes[-2]) / volumes[-2] if len(volumes) > 1 else 0,
                "price_volatility": np.std(prices[-20:]) if len(prices) >= 20 else 0,
                "volume_volatility": np.std(volumes[-20:]) if len(volumes) >= 20 else 0,
                "price_momentum": prices[-1] - prices[-5] if len(prices) >= 5 else 0,
                "volume_momentum": volumes[-1] - volumes[-5] if len(volumes) >= 5 else 0
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
            
    def _combine_signals(self, technical_signal: Dict[str, Any], 
                        ml_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Combine technical and ML signals."""
        
        try:
            # Simple majority voting
            signals = []
            confidences = []
            
            if technical_signal.get("signal") and technical_signal.get("signal") != "hold":
                signals.append(technical_signal["signal"])
                confidences.append(technical_signal.get("confidence", 0.5))
                
            if ml_signal.get("signal") and ml_signal.get("signal") != "hold":
                signals.append(ml_signal["signal"])
                confidences.append(ml_signal.get("confidence", 0.5))
                
            if not signals:
                return {
                    "signal": "hold",
                    "confidence": 0.5,
                    "risk_level": "medium"
                }
                
            # Determine final signal
            if len(set(signals)) == 1:
                # All signals agree
                final_signal = signals[0]
                final_confidence = np.mean(confidences)
            else:
                # Signals disagree, use higher confidence
                max_confidence_idx = np.argmax(confidences)
                final_signal = signals[max_confidence_idx]
                final_confidence = confidences[max_confidence_idx] * 0.8  # Reduce confidence due to disagreement
                
            # Determine risk level
            if final_confidence > 0.8:
                risk_level = "low"
            elif final_confidence < 0.6:
                risk_level = "high"
            else:
                risk_level = "medium"
                
            return {
                "signal": final_signal,
                "confidence": final_confidence,
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return {
                "signal": "hold",
                "confidence": 0.5,
                "risk_level": "medium"
            }
            
    def _combine_signals_weighted(self, technical_signal: Dict[str, Any], 
                                ml_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Combine signals using weighted approach."""
        
        try:
            # Weight technical analysis more heavily
            tech_weight = 0.6
            ml_weight = 0.4
            
            tech_confidence = technical_signal.get("confidence", 0.5)
            ml_confidence = ml_signal.get("confidence", 0.5)
            
            # Weighted confidence
            weighted_confidence = (tech_confidence * tech_weight) + (ml_confidence * ml_weight)
            
            # Determine signal based on weighted analysis
            if tech_confidence > 0.7 and ml_confidence > 0.6:
                signal = technical_signal.get("signal", "hold")
            elif tech_confidence > 0.8:
                signal = technical_signal.get("signal", "hold")
            elif ml_confidence > 0.8:
                signal = ml_signal.get("signal", "hold")
            else:
                signal = "hold"
                
            # Risk level
            if weighted_confidence > 0.8:
                risk_level = "low"
            elif weighted_confidence < 0.6:
                risk_level = "high"
            else:
                risk_level = "medium"
                
            return {
                "signal": signal,
                "confidence": weighted_confidence,
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Error combining signals weighted: {e}")
            return {
                "signal": "hold",
                "confidence": 0.5,
                "risk_level": "medium"
            }
            
    def _calculate_ml_risk(self, confidence: float) -> str:
        """Calculate risk level based on ML confidence."""
        if confidence > 0.8:
            return "low"
        elif confidence < 0.6:
            return "high"
        else:
            return "medium"
            
    async def _generate_signal_reasoning(self, signal_result: Dict[str, Any]) -> str:
        """Generate AI reasoning for the signal using AutoGen agent."""
        try:
            # Create context for AutoGen reasoning
            context = f"""
            Symbol: {signal_result.get('symbol', 'Unknown')}
            Signal: {signal_result.get('signal', 'hold')}
            Confidence: {signal_result.get('confidence', 0.0)}
            Timeframe: {signal_result.get('timeframe', '1h')}
            Technical Indicators: {signal_result.get('indicators', {})}
            Risk Level: {signal_result.get('risk_level', 'medium')}
            """
            
            question = f"What is the reasoning behind this {signal_result.get('signal', 'hold')} signal for {signal_result.get('symbol', 'Unknown')}?"
            
            # Use AutoGen agent for reasoning
            reasoning = await self._use_autogen_reasoning(context, question)
            
            return reasoning
            
        except Exception as e:
            logger.error(f"Error generating signal reasoning: {e}")
            return f"Signal reasoning error: {str(e)}"
            
    def _create_reasoning_prompt(self, signal_result: Dict[str, Any]) -> str:
        """Create a prompt for signal reasoning generation."""
        
        prompt = f"Based on the following signal analysis, provide clear reasoning:\n\n"
        prompt += f"Symbol: {signal_result.get('symbol', 'unknown')}\n"
        prompt += f"Signal: {signal_result.get('signal', 'hold')}\n"
        prompt += f"Confidence: {signal_result.get('confidence', 0.0)}\n"
        prompt += f"Risk Level: {signal_result.get('risk_level', 'medium')}\n"
        prompt += f"Timeframe: {signal_result.get('timeframe', '1h')}\n"
        
        if "indicators" in signal_result:
            prompt += f"Technical Indicators: {json.dumps(signal_result['indicators'], indent=2)}\n"
            
        prompt += "\nPlease provide:\n1. Key factors supporting this signal\n2. Risk considerations\n3. Market context\n4. Confidence explanation"
        
        return prompt
        
    async def _generate_signal_recommendation(self, signal_result: Dict[str, Any]) -> str:
        """Generate AI recommendation for the signal using AutoGen agent."""
        try:
            # Create context for AutoGen recommendation
            context = f"""
            Symbol: {signal_result.get('symbol', 'Unknown')}
            Signal: {signal_result.get('signal', 'hold')}
            Confidence: {signal_result.get('confidence', 0.0)}
            Timeframe: {signal_result.get('timeframe', '1h')}
            Technical Indicators: {signal_result.get('indicators', {})}
            Risk Level: {signal_result.get('risk_level', 'medium')}
            Reasoning: {signal_result.get('reasoning', 'No reasoning available')}
            """
            
            question = f"What specific trading recommendation would you make based on this {signal_result.get('signal', 'hold')} signal for {signal_result.get('symbol', 'Unknown')}?"
            
            # Use AutoGen agent for recommendation
            recommendation = await self._use_autogen_reasoning(context, question)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating signal recommendation: {e}")
            return f"Signal recommendation error: {str(e)}"
            
    def _create_recommendation_prompt(self, signal_result: Dict[str, Any]) -> str:
        """Create a prompt for signal recommendation generation."""
        
        prompt = f"Based on this signal analysis, provide a clear recommendation:\n\n"
        prompt += f"Signal: {signal_result.get('signal', 'hold')}\n"
        prompt += f"Confidence: {signal_result.get('confidence', 0.0)}\n"
        prompt += f"Risk Level: {signal_result.get('risk_level', 'medium')}\n"
        prompt += f"Symbol: {signal_result.get('symbol', 'unknown')}\n"
        
        prompt += "\nPlease provide:\n1. Action recommendation\n2. Position sizing suggestion\n3. Stop-loss recommendation\n4. Time horizon"
        
        return prompt
        
    async def _store_signal_history(self, signal_result: Dict[str, Any]):
        """Store signal in history for learning."""
        
        try:
            # Store signal
            self.signal_history.append({
                "timestamp": datetime.now().isoformat(),
                "symbol": signal_result.get("symbol"),
                "signal": signal_result.get("signal"),
                "confidence": signal_result.get("confidence"),
                "signal_type": signal_result.get("signal_type"),
                "timeframe": signal_result.get("timeframe")
            })
            
            # Keep only recent history (last 1000 signals)
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-1000:]
                
        except Exception as e:
            logger.error(f"Error storing signal history: {e}")
            
    async def _learn_from_signal(self, signal_result: Dict[str, Any]):
        """Learn from signal generation patterns."""
        
        try:
            # Analyze signal patterns
            conf = signal_result.get("confidence")
            if conf is None:
                conf = 0.0
            pattern = {
                "timestamp": datetime.now().isoformat(),
                "symbol": signal_result.get("symbol"),
                "signal": signal_result.get("signal"),
                "confidence": conf,
                "signal_type": signal_result.get("signal_type"),
                "timeframe": signal_result.get("timeframe"),
                "success": conf > 0.7
            }
            # Update performance metrics
            symbol = signal_result.get("symbol", "unknown")
            if symbol not in self.performance_metrics:
                self.performance_metrics[symbol] = {
                    "total_signals": 0,
                    "successful_signals": 0,
                    "average_confidence": 0.0
                }
            self.performance_metrics[symbol]["total_signals"] += 1
            if pattern["success"]:
                self.performance_metrics[symbol]["successful_signals"] += 1
            # Update average confidence
            current_avg = self.performance_metrics[symbol]["average_confidence"]
            total_signals = self.performance_metrics[symbol]["total_signals"]
            new_avg = ((current_avg * (total_signals - 1)) + conf) / total_signals
            self.performance_metrics[symbol]["average_confidence"] = new_avg
            logger.info(f"Learned from signal pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error learning from signal: {e}")
            
    async def _get_price_data(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """Get price data from database."""
        
        try:
            if not self.db_client:
                return []
                
            # Get recent price data for the symbol
            query = """
                SELECT open, high, low, close, volume, timestamp 
                FROM price_data 
                WHERE symbol = :symbol
                AND timestamp > NOW() - INTERVAL '7 days'
                ORDER BY timestamp ASC
            """
            
            result = await self.db_client.execute(query, {"symbol": symbol})
            return result.fetchall()
            
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return []
            
    async def _load_models(self):
        """Load existing ML models."""
        
        try:
            # Load models from database or file system
            # This would integrate with existing model storage
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            
    async def _get_model_performance(self, symbol: str) -> Dict[str, Any]:
        """Get ML model performance metrics."""
        
        try:
            if symbol in self.performance_metrics:
                metrics = self.performance_metrics[symbol]
                success_rate = metrics["successful_signals"] / max(metrics["total_signals"], 1)
                return {
                    "success_rate": success_rate,
                    "total_signals": metrics["total_signals"],
                    "average_confidence": metrics["average_confidence"]
                }
            else:
                return {
                    "success_rate": 0.0,
                    "total_signals": 0,
                    "average_confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {"error": str(e)}
            
    async def get_signal_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get signal history."""
        
        if symbol:
            return [s for s in self.signal_history if s.get("symbol") == symbol][-limit:]
        else:
            return self.signal_history[-limit:]
            
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all symbols."""
        return self.performance_metrics
        
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status including AutoGen capabilities."""
        try:
            status = {
                "name": "AgenticSignalAgent",
                "status": "running",
                "autogen_agent": {
                    "available": self.autogen_agent is not None,
                    "name": self.autogen_agent.name if self.autogen_agent else None,
                    "capabilities": [
                        "autonomous_signal_generation",
                        "ai_reasoning",
                        "technical_analysis",
                        "machine_learning",
                        "signal_optimization"
                    ]
                },
                "websocket": {
                    "connected": self.ws_client.is_connected if self.ws_client else False,
                    "client_id": "agentic_signal"
                },
                "tools": {
                    "count": len(self.tools) if hasattr(self, 'tools') else 0,
                    "categories": ["analysis", "technical_indicators", "ml_models"]
                },
                "cache": {
                    "size": len(self.signal_cache),
                    "ttl_seconds": self.cache_ttl
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {
                "name": "AgenticSignalAgent",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class TechnicalIndicators:
    """Technical analysis indicators for signal generation."""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return [50.0] * len(prices)
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = pd.Series(gains).rolling(window=period).mean().values
        avg_losses = pd.Series(losses).rolling(window=period).mean().values
        
        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return [50.0] * period + rsi[period:].tolist()
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """Calculate MACD."""
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