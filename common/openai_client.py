"""
OpenAI Client Module for VolexSwarm
Provides GPT integration for market commentary and advanced reasoning.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from openai import OpenAI
import tiktoken
import json

from .vault import get_vault_client
from .logging import get_logger

logger = get_logger("openai")

class VolexSwarmOpenAIClient:
    """OpenAI client for VolexSwarm with market commentary and reasoning capabilities."""
    
    def __init__(self):
        self.client = None
        self.model = "gpt-4o-mini"  # Default model
        self.max_tokens = 2000
        self.temperature = 0.3  # Lower temperature for more consistent reasoning
        self.encoding = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client with API key from Vault."""
        try:
            vault_client = get_vault_client()
            openai_config = vault_client.get_secret("api_keys/openai")
            
            if not openai_config or not openai_config.get("api_key"):
                logger.warning("OpenAI API key not found in Vault")
                return
            
            api_key = openai_config["api_key"]
            self.client = OpenAI(api_key=api_key)
            
            # Initialize tokenizer
            try:
                self.encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # Fallback to cl100k_base encoding
                self.encoding = tiktoken.get_encoding("cl100k_base")
            
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available."""
        return self.client is not None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not self.encoding:
            return len(text.split())  # Rough estimate
        return len(self.encoding.encode(text))
    
    def generate_market_commentary(self, 
                                 symbol: str, 
                                 price_data: Dict[str, Any],
                                 technical_indicators: Dict[str, Any],
                                 market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate market commentary using GPT.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSD')
            price_data: Current price and volume data
            technical_indicators: Technical analysis indicators
            market_context: Additional market context (optional)
        
        Returns:
            Dict containing commentary and insights
        """
        if not self.is_available():
            return {
                "commentary": "OpenAI integration not available",
                "insights": [],
                "sentiment": "neutral",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Prepare market data for GPT
            market_info = {
                "symbol": symbol,
                "current_price": price_data.get("close", 0),
                "price_change_24h": price_data.get("change_24h", 0),
                "volume_24h": price_data.get("volume", 0),
                "technical_indicators": technical_indicators,
                "market_context": market_context or {}
            }
            
            # Create prompt for market commentary
            prompt = self._create_market_commentary_prompt(market_info)
            
            # Generate commentary
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_market_analyst_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            commentary_text = response.choices[0].message.content
            
            # Parse and structure the response
            structured_response = self._parse_market_commentary(commentary_text, market_info)
            
            logger.info(f"Generated market commentary for {symbol}")
            return structured_response
            
        except Exception as e:
            logger.error(f"Failed to generate market commentary: {e}")
            return {
                "commentary": f"Error generating commentary: {str(e)}",
                "insights": [],
                "sentiment": "neutral",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_trading_decision(self,
                               symbol: str,
                               proposed_action: str,
                               signal_data: Dict[str, Any],
                               market_data: Dict[str, Any],
                               risk_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze trading decision using GPT for advanced reasoning.
        
        Args:
            symbol: Trading symbol
            proposed_action: Proposed action (buy/sell/hold)
            signal_data: Signal generation data
            market_data: Current market data
            risk_parameters: Risk management parameters
        
        Returns:
            Dict containing analysis and recommendations
        """
        if not self.is_available():
            return {
                "analysis": "OpenAI integration not available",
                "recommendation": proposed_action,
                "reasoning": "No advanced reasoning available",
                "confidence": signal_data.get("confidence", 0.0),
                "risk_assessment": "Unable to assess risk",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Prepare decision context
            decision_context = {
                "symbol": symbol,
                "proposed_action": proposed_action,
                "signal_data": signal_data,
                "market_data": market_data,
                "risk_parameters": risk_parameters
            }
            
            # Create prompt for decision analysis
            prompt = self._create_decision_analysis_prompt(decision_context)
            
            # Generate analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_trading_analyst_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse and structure the response
            structured_response = self._parse_decision_analysis(analysis_text, decision_context)
            
            logger.info(f"Generated trading decision analysis for {symbol}")
            return structured_response
            
        except Exception as e:
            logger.error(f"Failed to analyze trading decision: {e}")
            return {
                "analysis": f"Error analyzing decision: {str(e)}",
                "recommendation": proposed_action,
                "reasoning": "No reasoning available",
                "confidence": signal_data.get("confidence", 0.0),
                "risk_assessment": "Unable to assess risk",
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_strategy_insights(self,
                                 strategy_name: str,
                                 performance_data: Dict[str, Any],
                                 market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate strategy insights and optimization suggestions.
        
        Args:
            strategy_name: Name of the trading strategy
            performance_data: Historical performance metrics
            market_conditions: Current market conditions
        
        Returns:
            Dict containing insights and recommendations
        """
        if not self.is_available():
            return {
                "insights": "OpenAI integration not available",
                "recommendations": [],
                "optimization_suggestions": [],
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Prepare strategy context
            strategy_context = {
                "strategy_name": strategy_name,
                "performance_data": performance_data,
                "market_conditions": market_conditions
            }
            
            # Create prompt for strategy analysis
            prompt = self._create_strategy_analysis_prompt(strategy_context)
            
            # Generate insights
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_strategy_analyst_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            insights_text = response.choices[0].message.content
            
            # Parse and structure the response
            structured_response = self._parse_strategy_insights(insights_text, strategy_context)
            
            logger.info(f"Generated strategy insights for {strategy_name}")
            return structured_response
            
        except Exception as e:
            logger.error(f"Failed to generate strategy insights: {e}")
            return {
                "insights": f"Error generating insights: {str(e)}",
                "recommendations": [],
                "optimization_suggestions": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_market_commentary_prompt(self, market_info: Dict[str, Any]) -> str:
        """Create prompt for market commentary generation."""
        return f"""
Analyze the following market data for {market_info['symbol']} and provide:

1. **Market Commentary**: A concise analysis of current market conditions
2. **Key Insights**: 3-5 important observations about price action, volume, and technical indicators
3. **Sentiment Assessment**: Overall market sentiment (bullish/bearish/neutral) with confidence level
4. **Risk Factors**: Potential risks or concerns to watch

Market Data:
- Current Price: ${market_info['current_price']:,.2f}
- 24h Change: {market_info['price_change_24h']:+.2f}%
- 24h Volume: {market_info['volume_24h']:,.0f}
- Technical Indicators: {json.dumps(market_info['technical_indicators'], indent=2)}

Provide your analysis in a structured format that can be easily parsed.
"""
    
    def _create_decision_analysis_prompt(self, decision_context: Dict[str, Any]) -> str:
        """Create prompt for trading decision analysis."""
        return f"""
Analyze the following trading decision for {decision_context['symbol']}:

**Proposed Action**: {decision_context['proposed_action'].upper()}
**Signal Confidence**: {decision_context['signal_data'].get('confidence', 0):.1%}

Signal Data: {json.dumps(decision_context['signal_data'], indent=2)}
Market Data: {json.dumps(decision_context['market_data'], indent=2)}
Risk Parameters: {json.dumps(decision_context['risk_parameters'], indent=2)}

Provide:
1. **Decision Analysis**: Evaluate the proposed action
2. **Recommendation**: Confirm, modify, or reject the action
3. **Reasoning**: Detailed explanation of your recommendation
4. **Risk Assessment**: Current risk level and concerns
5. **Confidence Level**: Your confidence in this analysis

Format your response for easy parsing.
"""
    
    def _create_strategy_analysis_prompt(self, strategy_context: Dict[str, Any]) -> str:
        """Create prompt for strategy analysis."""
        return f"""
Analyze the following trading strategy performance:

**Strategy**: {strategy_context['strategy_name']}
**Performance Data**: {json.dumps(strategy_context['performance_data'], indent=2)}
**Market Conditions**: {json.dumps(strategy_context['market_conditions'], indent=2)}

Provide:
1. **Performance Insights**: Key observations about strategy performance
2. **Optimization Recommendations**: Specific suggestions for improvement
3. **Market Adaptation**: How the strategy should adapt to current conditions
4. **Risk Management**: Risk assessment and mitigation suggestions

Format your response for easy parsing.
"""
    
    def _get_market_analyst_system_prompt(self) -> str:
        """Get system prompt for market analyst role."""
        return """You are an expert cryptocurrency market analyst with deep knowledge of technical analysis, market psychology, and trading dynamics. 

Your role is to provide clear, actionable market commentary that helps traders understand current market conditions and make informed decisions.

Key principles:
- Be objective and data-driven
- Focus on actionable insights
- Consider both technical and fundamental factors
- Assess risk appropriately
- Provide clear, structured analysis

Always format your responses in a way that can be easily parsed by trading systems."""
    
    def _get_trading_analyst_system_prompt(self) -> str:
        """Get system prompt for trading analyst role."""
        return """You are an expert trading analyst specializing in cryptocurrency markets. Your role is to evaluate trading decisions and provide advanced reasoning for trade execution.

Key responsibilities:
- Evaluate proposed trading actions
- Assess risk-reward ratios
- Consider market context and conditions
- Provide clear reasoning for recommendations
- Identify potential issues or concerns

Always prioritize risk management and provide structured, actionable advice."""
    
    def _get_strategy_analyst_system_prompt(self) -> str:
        """Get system prompt for strategy analyst role."""
        return """You are an expert trading strategy analyst with deep knowledge of quantitative trading, backtesting, and strategy optimization.

Your role is to:
- Analyze strategy performance
- Identify optimization opportunities
- Suggest parameter adjustments
- Assess strategy robustness
- Provide actionable recommendations

Focus on data-driven insights and practical improvements."""
    
    def _parse_market_commentary(self, commentary_text: str, market_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse market commentary response into structured format."""
        try:
            # Extract sentiment and confidence
            sentiment = "neutral"
            confidence = 0.5
            
            if "bullish" in commentary_text.lower():
                sentiment = "bullish"
            elif "bearish" in commentary_text.lower():
                sentiment = "bearish"
            
            # Extract insights (simple parsing)
            insights = []
            lines = commentary_text.split('\n')
            for line in lines:
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    insights.append(line.strip()[1:].strip())
            
            return {
                "commentary": commentary_text,
                "insights": insights[:5],  # Limit to 5 insights
                "sentiment": sentiment,
                "confidence": confidence,
                "symbol": market_info["symbol"],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to parse market commentary: {e}")
            return {
                "commentary": commentary_text,
                "insights": [],
                "sentiment": "neutral",
                "confidence": 0.5,
                "symbol": market_info["symbol"],
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_decision_analysis(self, analysis_text: str, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse decision analysis response into structured format."""
        try:
            # Extract recommendation
            recommendation = decision_context["proposed_action"]
            if "confirm" in analysis_text.lower():
                recommendation = decision_context["proposed_action"]
            elif "modify" in analysis_text.lower() or "adjust" in analysis_text.lower():
                recommendation = "modify"
            elif "reject" in analysis_text.lower() or "cancel" in analysis_text.lower():
                recommendation = "reject"
            
            # Extract confidence
            confidence = decision_context["signal_data"].get("confidence", 0.0)
            
            return {
                "analysis": analysis_text,
                "recommendation": recommendation,
                "reasoning": analysis_text,
                "confidence": confidence,
                "risk_assessment": "Standard risk assessment",
                "symbol": decision_context["symbol"],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to parse decision analysis: {e}")
            return {
                "analysis": analysis_text,
                "recommendation": decision_context["proposed_action"],
                "reasoning": analysis_text,
                "confidence": decision_context["signal_data"].get("confidence", 0.0),
                "risk_assessment": "Unable to assess risk",
                "symbol": decision_context["symbol"],
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_strategy_insights(self, insights_text: str, strategy_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse strategy insights response into structured format."""
        try:
            # Extract recommendations and suggestions
            recommendations = []
            optimization_suggestions = []
            
            lines = insights_text.split('\n')
            for line in lines:
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    if "optimize" in line.lower() or "parameter" in line.lower():
                        optimization_suggestions.append(line.strip()[1:].strip())
                    else:
                        recommendations.append(line.strip()[1:].strip())
            
            return {
                "insights": insights_text,
                "recommendations": recommendations[:5],
                "optimization_suggestions": optimization_suggestions[:5],
                "strategy_name": strategy_context["strategy_name"],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to parse strategy insights: {e}")
            return {
                "insights": insights_text,
                "recommendations": [],
                "optimization_suggestions": [],
                "strategy_name": strategy_context["strategy_name"],
                "timestamp": datetime.now().isoformat()
            }


# Global OpenAI client instance
openai_client = None


def get_openai_client() -> VolexSwarmOpenAIClient:
    """Get global OpenAI client instance."""
    global openai_client
    if openai_client is None:
        openai_client = VolexSwarmOpenAIClient()
    return openai_client


def is_openai_available() -> bool:
    """Check if OpenAI integration is available."""
    client = get_openai_client()
    return client.is_available() 