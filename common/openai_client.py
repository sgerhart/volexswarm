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
import asyncio

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
            openai_config = vault_client.get_secret("openai/api_key")
            
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
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4
        
        try:
            return len(self.encoding.encode(text))
        except Exception:
            return len(text) // 4
    
    async def generate_completion(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Generate async completion for conversational AI."""
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        try:
            # Run the synchronous call in a thread pool to make it async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens or self.max_tokens,
                    temperature=temperature or self.temperature
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate completion: {e}")
            raise Exception(f"OpenAI completion failed: {str(e)}")
    
    def generate_market_commentary(self, market_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market commentary using GPT."""
        if not self.client:
            logger.warning("OpenAI client not available")
            return {
                "commentary": "OpenAI client not available for market commentary",
                "insights": [],
                "sentiment": "neutral",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Validate required fields
            required_fields = ['symbol', 'current_price', 'price_change_24h', 'volume_24h']
            for field in required_fields:
                if field not in market_info:
                    logger.warning(f"Missing required field for market commentary: {field}")
                    return {
                        "commentary": f"Missing required market data: {field}",
                        "insights": [],
                        "sentiment": "neutral",
                        "confidence": 0.0,
                        "timestamp": datetime.now().isoformat()
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
            
            logger.info(f"Generated market commentary for {market_info['symbol']}")
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
    
    def analyze_trading_decision(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a trading decision using GPT."""
        if not self.client:
            logger.warning("OpenAI client not available")
            return {
                "recommendation": "hold",
                "reasoning": "OpenAI client not available for decision analysis",
                "confidence": 0.0,
                "risk_assessment": "unknown",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Validate required fields
            required_fields = ['symbol', 'proposed_action', 'signal_data', 'market_data']
            for field in required_fields:
                if field not in decision_context:
                    logger.warning(f"Missing required field for decision analysis: {field}")
                    return {
                        "recommendation": "hold",
                        "reasoning": f"Missing required decision context: {field}",
                        "confidence": 0.0,
                        "risk_assessment": "unknown",
                        "timestamp": datetime.now().isoformat()
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
            
            logger.info(f"Analyzed trading decision for {decision_context['symbol']}")
            return structured_response
            
        except Exception as e:
            logger.error(f"Failed to analyze trading decision: {e}")
            return {
                "recommendation": "hold",
                "reasoning": f"Error analyzing decision: {str(e)}",
                "confidence": 0.0,
                "risk_assessment": "unknown",
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_strategy_insights(self, strategy_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategy insights using GPT."""
        if not self.client:
            logger.warning("OpenAI client not available")
            return {
                "insights": "OpenAI client not available for strategy insights",
                "recommendations": [],
                "optimization_suggestions": [],
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Validate required fields
            required_fields = ['strategy_name', 'performance_data']
            for field in required_fields:
                if field not in strategy_context:
                    logger.warning(f"Missing required field for strategy insights: {field}")
                    return {
                        "insights": f"Missing required strategy context: {field}",
                        "recommendations": [],
                        "optimization_suggestions": [],
                        "timestamp": datetime.now().isoformat()
                    }
            
            strategy_name = strategy_context['strategy_name']
            
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

Your analysis should be:
- Data-driven and objective
- Clear and actionable
- Risk-aware
- Based on established trading principles

Focus on providing insights that help traders make informed decisions while managing risk effectively."""
    
    def _get_trading_analyst_system_prompt(self) -> str:
        """Get system prompt for trading analyst role."""
        return """You are an expert trading decision analyst specializing in cryptocurrency markets. 

Your role is to:
- Evaluate proposed trading actions objectively
- Assess risk vs reward scenarios
- Provide clear recommendations (confirm/modify/reject)
- Explain your reasoning thoroughly
- Consider market conditions and timing

Always prioritize risk management and capital preservation in your analysis."""
    
    def _get_strategy_analyst_system_prompt(self) -> str:
        """Get system prompt for strategy analyst role."""
        return """You are an expert trading strategy analyst with deep knowledge of algorithmic trading and strategy optimization.

Your analysis should focus on:
- Strategy performance evaluation
- Identifying strengths and weaknesses
- Optimization opportunities
- Market adaptation recommendations
- Risk management improvements

Provide actionable insights that can be implemented to improve strategy performance."""
    
    def _parse_market_commentary(self, commentary_text: str, market_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure market commentary response."""
        # Basic parsing - in a production system, this would be more sophisticated
        lines = commentary_text.split('\n')
        
        commentary = ""
        insights = []
        sentiment = "neutral"
        confidence = 0.5
        
        current_section = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "market commentary" in line.lower():
                current_section = "commentary"
            elif "key insights" in line.lower():
                current_section = "insights"
            elif "sentiment" in line.lower():
                current_section = "sentiment"
                # Extract sentiment
                if "bullish" in line.lower():
                    sentiment = "bullish"
                elif "bearish" in line.lower():
                    sentiment = "bearish"
                else:
                    sentiment = "neutral"
            elif current_section == "commentary" and not line.startswith('**'):
                commentary += line + " "
            elif current_section == "insights" and line.startswith('-'):
                insights.append(line[1:].strip())
        
        return {
            "commentary": commentary.strip(),
            "insights": insights,
            "sentiment": sentiment,
            "confidence": confidence,
            "risk_factors": [],
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_decision_analysis(self, analysis_text: str, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure decision analysis response."""
        # Basic parsing - in a production system, this would be more sophisticated
        lines = analysis_text.split('\n')
        
        recommendation = "hold"
        reasoning = ""
        confidence = 0.5
        risk_assessment = "medium"
        
        for line in lines:
            line = line.strip().lower()
            if "confirm" in line and "recommendation" in line:
                recommendation = "confirm"
            elif "reject" in line and "recommendation" in line:
                recommendation = "reject"
            elif "modify" in line and "recommendation" in line:
                recommendation = "modify"
            elif "reasoning" in line:
                reasoning = line.split(':', 1)[-1].strip() if ':' in line else line
        
        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "confidence": confidence,
            "risk_assessment": risk_assessment,
            "modifications": [],
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_strategy_insights(self, insights_text: str, strategy_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure strategy insights response."""
        # Basic parsing - in a production system, this would be more sophisticated
        lines = insights_text.split('\n')
        
        insights = ""
        recommendations = []
        optimization_suggestions = []
        
        current_section = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "performance insights" in line.lower():
                current_section = "insights"
            elif "optimization" in line.lower():
                current_section = "optimization"
            elif "recommendations" in line.lower():
                current_section = "recommendations"
            elif current_section == "insights" and not line.startswith('**'):
                insights += line + " "
            elif current_section == "optimization" and line.startswith('-'):
                optimization_suggestions.append(line[1:].strip())
            elif current_section == "recommendations" and line.startswith('-'):
                recommendations.append(line[1:].strip())
        
        return {
            "insights": insights.strip(),
            "recommendations": recommendations,
            "optimization_suggestions": optimization_suggestions,
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