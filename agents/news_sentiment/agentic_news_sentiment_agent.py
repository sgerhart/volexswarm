"""
VolexSwarm Agentic News Sentiment Agent - Autonomous News Analysis
Transforms the FastAPI news sentiment agent into an intelligent AutoGen AssistantAgent
with autonomous news analysis and sentiment-based trading signal generation.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
import aiohttp
import json
import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import feedparser
from bs4 import BeautifulSoup

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client
from common.logging import get_logger
from common.websocket_client import AgentWebSocketClient, MessageType
from agents.agentic_framework.agent_templates import NewsSentimentAgent
from agents.agentic_framework.mcp_tools import MCPToolRegistry, MCPTool

logger = get_logger("agentic_news_sentiment")

@dataclass
class NewsArticle:
    """News article data structure."""
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"
    impact_score: float = 0.0
    relevant_keywords: List[str] = None
    trading_implications: List[str] = None

@dataclass
class SentimentAnalysisRequest:
    """Request for sentiment analysis."""
    text: str
    symbols: Optional[List[str]] = None
    context: Optional[str] = None

@dataclass
class SentimentAnalysisResult:
    """Result of sentiment analysis."""
    text: str
    sentiment_score: float
    sentiment_label: str
    confidence: float
    keywords: List[str]
    entities: List[str]
    impact_score: float
    trading_signals: List[Dict[str, Any]]

@dataclass
class NewsSignalRequest:
    """Request for news-based trading signals."""
    symbols: List[str]
    timeframe: str = "1h"
    sentiment_threshold: float = 0.3
    impact_threshold: float = 0.5

@dataclass
class NewsSignalResult:
    """Result of news-based trading signal generation."""
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    confidence: float
    sentiment_score: float
    impact_score: float
    reasoning: str
    news_articles: List[Dict[str, Any]]
    timestamp: datetime

class AgenticNewsSentimentAgent:
    """Intelligent News Sentiment Agent using AutoGen AssistantAgent."""
    
    def __init__(self):
        """Initialize the agentic news sentiment agent."""
        self.vault_client = None
        self.db_client = None
        self.ws_client = None
        self.agent = None
        self.tool_registry = None
        self.sentiment_analyzer = None
        self.news_collector = None
        self.signal_generator = None
        self.news_sources = self._initialize_news_sources()
        self.crypto_keywords = self._initialize_crypto_keywords()
        self.collected_articles = []
        
        # Initialize with default config to avoid Vault dependency during __init__
        self._initialize_agent_with_defaults()
        
    def _initialize_agent_with_defaults(self):
        """Initialize the AutoGen AssistantAgent with default configuration."""
        try:
            # Use default configuration to avoid Vault dependency during __init__
            default_config = {
                "config_list": [{
                    "model": "gpt-4o-mini",
                    "api_key": "mock-key-for-testing"
                }],
                "temperature": 0.1,
                "timeout": 120
            }
            
            # Create the AutoGen agent
            self.agent = NewsSentimentAgent(default_config)
            
            # Initialize MCP tool registry
            self.tool_registry = MCPToolRegistry()
            self._register_news_tools()
            
            # Initialize sentiment analyzer
            self.sentiment_analyzer = NewsSentimentAnalyzer()
            
            # Initialize news collector
            self.news_collector = NewsCollector()
            
            # Initialize signal generator
            self.signal_generator = NewsSignalGenerator(self.sentiment_analyzer)
            
            logger.info("Agentic News Sentiment Agent initialized with defaults successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agentic news sentiment agent with defaults: {e}")
            raise
    
    def _initialize_agent(self):
        """Initialize the AutoGen AssistantAgent with Vault configuration."""
        try:
            # Get OpenAI configuration from vault
            config = get_agent_config("news_sentiment")
            openai_config = {
                "config_list": [{
                    "model": config.get("openai_model", "gpt-4"),
                    "api_key": config.get("openai_api_key")
                }],
                "temperature": 0.1,
                "timeout": 120
            }
            
            # Create the AutoGen agent with Vault config
            self.agent = NewsSentimentAgent(openai_config)
            
            logger.info("Agentic News Sentiment Agent reinitialized with Vault configuration")
            
        except Exception as e:
            logger.error(f"Failed to reinitialize agentic news sentiment agent with Vault config: {e}")
            # Don't raise here, keep using default config
    
    def _register_news_tools(self):
        """Register news-specific MCP tools."""
        try:
            # Register news analysis tools
            self.tool_registry.register_tool(MCPTool(
                name="analyze_sentiment",
                description="Analyze sentiment of text content",
                function=self.analyze_sentiment,
                parameters={
                    "text": {"type": "string", "description": "Text to analyze"},
                    "symbols": {"type": "array", "description": "Trading symbols to consider"}
                },
                required_permissions=["news_analysis"],
                category="news_analysis"
            ))
            
            self.tool_registry.register_tool(MCPTool(
                name="generate_news_signals",
                description="Generate trading signals based on news sentiment",
                function=self.generate_news_signals,
                parameters={
                    "symbols": {"type": "array", "description": "Trading symbols"},
                    "timeframe": {"type": "string", "description": "Analysis timeframe"},
                    "sentiment_threshold": {"type": "number", "description": "Sentiment threshold"}
                },
                required_permissions=["news_analysis", "signal_generation"],
                category="news_analysis"
            ))
            
            self.tool_registry.register_tool(MCPTool(
                name="collect_news",
                description="Collect news articles from various sources",
                function=self.collect_news,
                parameters={},
                required_permissions=["news_collection"],
                category="news_analysis"
            ))
            
            self.tool_registry.register_tool(MCPTool(
                name="get_sentiment_summary",
                description="Get sentiment summary for recent news",
                function=self.get_sentiment_summary,
                parameters={
                    "hours": {"type": "number", "description": "Hours to look back"}
                },
                required_permissions=["news_analysis"],
                category="news_analysis"
            ))
            
            self.tool_registry.register_tool(MCPTool(
                name="analyze_news_impact",
                description="Analyze impact of news on specific symbols",
                function=self.analyze_news_impact,
                parameters={
                    "symbol": {"type": "string", "description": "Trading symbol"},
                    "timeframe": {"type": "string", "description": "Analysis timeframe"}
                },
                required_permissions=["news_analysis"],
                category="news_analysis"
            ))
            
            logger.info("News analysis tools registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register news tools: {e}")
            raise
    
    def _initialize_news_sources(self) -> Dict[str, List[str]]:
        """Initialize news sources configuration."""
        return {
            'crypto_news': [
                'https://cointelegraph.com/rss',
                'https://coindesk.com/arc/outboundfeeds/rss/',
                'https://cryptonews.com/news/feed/',
                'https://bitcoinmagazine.com/.rss/full/'
            ],
            'financial_news': [
                'https://feeds.reuters.com/reuters/businessNews',
                'https://feeds.bloomberg.com/markets/news.rss',
                'https://www.ft.com/rss/home'
            ],
            'reddit': [
                'https://www.reddit.com/r/cryptocurrency/.rss',
                'https://www.reddit.com/r/bitcoin/.rss',
                'https://www.reddit.com/r/ethereum/.rss'
            ]
        }
    
    def _initialize_crypto_keywords(self) -> List[str]:
        """Initialize cryptocurrency keywords for filtering."""
        return [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency', 'blockchain',
            'defi', 'nft', 'altcoin', 'token', 'coin', 'mining', 'wallet', 'exchange',
            'binance', 'coinbase', 'kraken', 'solana', 'cardano', 'polkadot', 'avalanche'
        ]
    
    async def initialize(self):
        """Initialize the agent with external services."""
        try:
            # Initialize Vault client
            self.vault_client = get_vault_client()
            logger.info("Vault client initialized")
            
            # Initialize database client
            self.db_client = get_db_client()
            logger.info("Database client initialized")
            
            # Reinitialize agent with Vault configuration
            self._initialize_agent()
            
            # Initialize WebSocket client
            self.ws_client = AgentWebSocketClient("agentic_news_sentiment")
            await self.ws_client.connect()
            logger.info("WebSocket client connected")
            
            # Initialize news collector
            await self.news_collector.initialize()
            
            # Start news collection loop
            asyncio.create_task(self._news_collection_loop())
            
            # Start health monitoring
            asyncio.create_task(self._health_monitor_loop())
            
            logger.info("Agentic News Sentiment Agent fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize agentic news sentiment agent: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the agent gracefully."""
        try:
            if self.news_collector:
                await self.news_collector.close()
            if self.ws_client:
                await self.ws_client.disconnect()
            logger.info("Agentic News Sentiment Agent shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _health_monitor_loop(self):
        """Background task to send periodic health updates."""
        while True:
            try:
                if self.ws_client and self.ws_client.is_connected:
                    health_data = {
                        "status": "healthy",
                        "agent_type": "agentic_news_sentiment",
                        "db_connected": self.db_client is not None,
                        "vault_connected": self.vault_client is not None,
                        "news_collection_active": True,
                        "articles_collected": len(self.collected_articles),
                        "last_health_check": datetime.utcnow().isoformat()
                    }
                    
                    await self.ws_client.send_health_update(health_data)
                    logger.debug("Sent health update to Meta Agent")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _news_collection_loop(self):
        """Background task to continuously collect news."""
        while True:
            try:
                # Collect news from all sources
                articles = await self.collect_news()
                
                # Analyze sentiment for new articles
                for article in articles:
                    sentiment_result = await self.analyze_sentiment(
                        SentimentAnalysisRequest(text=f"{article.title} {article.content}")
                    )
                    article.sentiment_score = sentiment_result.sentiment_score
                    article.sentiment_label = sentiment_result.sentiment_label
                    article.impact_score = sentiment_result.impact_score
                    article.relevant_keywords = sentiment_result.keywords
                
                # Store articles
                await self._store_articles(articles)
                
                # Add to collected articles
                self.collected_articles.extend(articles)
                
                # Keep only recent articles (last 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.collected_articles = [
                    article for article in self.collected_articles 
                    if article.published_at > cutoff_time
                ]
                
                logger.info(f"Collected and analyzed {len(articles)} new articles")
                
                # Wait 5 minutes before next collection
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"News collection error: {e}")
                await asyncio.sleep(300)
    
    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResult:
        """Autonomously analyze sentiment using intelligent reasoning."""
        try:
            # Create sentiment analysis context
            context = {
                "text_length": len(request.text),
                "symbols": request.symbols or [],
                "context": request.context or "general",
                "crypto_keywords_present": self._extract_crypto_keywords(request.text)
            }
            
            # Generate sentiment analysis prompt
            prompt = self._generate_sentiment_analysis_prompt(context, request.text)
            
            # Get agent reasoning
            response = await self._get_agent_response(prompt)
            
            # Perform technical sentiment analysis
            technical_result = self.sentiment_analyzer.analyze_sentiment(request.text)
            
            # Combine agent reasoning with technical analysis
            sentiment_score = technical_result['sentiment_score']
            sentiment_label = technical_result['sentiment_label']
            confidence = response.get("confidence", 0.8)
            keywords = technical_result['keywords']
            entities = technical_result.get('entities', [])
            impact_score = technical_result['impact_score']
            
            # Generate trading signals based on agent reasoning
            trading_signals = self._generate_trading_signals_from_sentiment(
                sentiment_score, impact_score, request.symbols, response
            )
            
            result = SentimentAnalysisResult(
                text=request.text,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=confidence,
                keywords=keywords,
                entities=entities,
                impact_score=impact_score,
                trading_signals=trading_signals
            )
            
            logger.info(f"Sentiment analysis completed with confidence {confidence}")
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return SentimentAnalysisResult(
                text=request.text,
                sentiment_score=0.0,
                sentiment_label="neutral",
                confidence=0.0,
                keywords=[],
                entities=[],
                impact_score=0.0,
                trading_signals=[]
            )
    
    async def generate_news_signals(self, request: NewsSignalRequest) -> List[NewsSignalResult]:
        """Autonomously generate news-based trading signals using intelligent analysis."""
        try:
            # Create signal generation context
            context = {
                "symbols": request.symbols,
                "timeframe": request.timeframe,
                "sentiment_threshold": request.sentiment_threshold,
                "impact_threshold": request.impact_threshold,
                "available_articles": len(self.collected_articles),
                "recent_articles": len([a for a in self.collected_articles 
                                     if a.published_at > datetime.utcnow() - timedelta(hours=1)])
            }
            
            # Generate signal generation prompt
            prompt = self._generate_signal_generation_prompt(context)
            
            # Get agent reasoning
            response = await self._get_agent_response(prompt)
            
            # Generate signals using the signal generator
            signals = self.signal_generator.generate_signals(
                self.collected_articles,
                request.symbols,
                request.sentiment_threshold,
                request.impact_threshold
            )
            
            # Enhance signals with agent reasoning
            enhanced_signals = []
            for signal in signals:
                enhanced_signal = NewsSignalResult(
                    symbol=signal.symbol,
                    signal_type=signal.signal_type,
                    confidence=signal.confidence * response.get("confidence_multiplier", 1.0),
                    sentiment_score=signal.sentiment_score,
                    impact_score=signal.impact_score,
                    reasoning=f"{signal.reasoning} {response.get('additional_reasoning', '')}",
                    news_articles=signal.news_articles,
                    timestamp=signal.timestamp
                )
                enhanced_signals.append(enhanced_signal)
            
            logger.info(f"Generated {len(enhanced_signals)} news-based trading signals")
            return enhanced_signals
            
        except Exception as e:
            logger.error(f"News signal generation failed: {e}")
            return []
    
    async def collect_news(self) -> List[NewsArticle]:
        """Autonomously collect news from various sources."""
        try:
            articles = []
            
            # Collect from RSS feeds
            for source_type, urls in self.news_sources.items():
                for url in urls:
                    try:
                        if source_type == 'reddit':
                            reddit_articles = await self.news_collector.fetch_reddit_posts(url)
                            for article_data in reddit_articles:
                                article = NewsArticle(
                                    title=article_data.get('title', ''),
                                    content=article_data.get('content', ''),
                                    source=f"reddit_{url.split('/')[-2]}",
                                    url=article_data.get('url', ''),
                                    published_at=article_data.get('published_at', datetime.utcnow())
                                )
                                articles.append(article)
                        else:
                            rss_articles = await self.news_collector.fetch_rss_feed(url)
                            for article_data in rss_articles:
                                article = NewsArticle(
                                    title=article_data.get('title', ''),
                                    content=article_data.get('content', ''),
                                    source=source_type,
                                    url=article_data.get('url', ''),
                                    published_at=article_data.get('published_at', datetime.utcnow())
                                )
                                articles.append(article)
                    except Exception as e:
                        logger.warning(f"Failed to collect from {url}: {e}")
                        continue
            
            # Filter articles for crypto relevance
            relevant_articles = [
                article for article in articles
                if self._is_crypto_relevant(article.title + " " + article.content)
            ]
            
            logger.info(f"Collected {len(relevant_articles)} relevant articles from {len(articles)} total")
            return relevant_articles
            
        except Exception as e:
            logger.error(f"News collection failed: {e}")
            return []
    
    async def get_sentiment_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get sentiment summary with intelligent analysis."""
        try:
            # Get articles from the specified time period
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_articles = [
                article for article in self.collected_articles
                if article.published_at > cutoff_time
            ]
            
            # Create summary context
            context = {
                "total_articles": len(recent_articles),
                "time_period": f"last {hours} hours",
                "sentiment_distribution": self._calculate_sentiment_distribution(recent_articles),
                "top_keywords": self._extract_top_keywords(recent_articles),
                "impact_scores": [article.impact_score for article in recent_articles]
            }
            
            # Generate summary prompt
            prompt = self._generate_sentiment_summary_prompt(context)
            
            # Get agent analysis
            response = await self._get_agent_response(prompt)
            
            # Calculate technical metrics
            sentiment_scores = [article.sentiment_score for article in recent_articles]
            impact_scores = [article.impact_score for article in recent_articles]
            
            summary = {
                "time_period": f"last {hours} hours",
                "total_articles": len(recent_articles),
                "average_sentiment": np.mean(sentiment_scores) if sentiment_scores else 0.0,
                "sentiment_volatility": np.std(sentiment_scores) if sentiment_scores else 0.0,
                "average_impact": np.mean(impact_scores) if impact_scores else 0.0,
                "sentiment_distribution": context["sentiment_distribution"],
                "top_keywords": context["top_keywords"],
                "agent_insights": response.get("insights", []),
                "market_mood": response.get("market_mood", "neutral"),
                "trading_implications": response.get("trading_implications", [])
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get sentiment summary: {e}")
            return {"error": str(e)}
    
    async def analyze_news_impact(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        """Analyze news impact on specific symbol."""
        try:
            # Get recent articles mentioning the symbol
            cutoff_time = datetime.utcnow() - timedelta(hours=int(timeframe[:-1]) if timeframe.endswith('h') else 24)
            symbol_articles = [
                article for article in self.collected_articles
                if article.published_at > cutoff_time and 
                symbol.lower() in (article.title + " " + article.content).lower()
            ]
            
            # Create impact analysis context
            context = {
                "symbol": symbol,
                "timeframe": timeframe,
                "articles_count": len(symbol_articles),
                "sentiment_scores": [article.sentiment_score for article in symbol_articles],
                "impact_scores": [article.impact_score for article in symbol_articles]
            }
            
            # Generate impact analysis prompt
            prompt = self._generate_impact_analysis_prompt(context)
            
            # Get agent analysis
            response = await self._get_agent_response(prompt)
            
            # Calculate technical metrics
            sentiment_scores = context["sentiment_scores"]
            impact_scores = context["impact_scores"]
            
            impact_analysis = {
                "symbol": symbol,
                "timeframe": timeframe,
                "articles_count": len(symbol_articles),
                "average_sentiment": np.mean(sentiment_scores) if sentiment_scores else 0.0,
                "sentiment_trend": self._calculate_sentiment_trend(symbol_articles),
                "average_impact": np.mean(impact_scores) if impact_scores else 0.0,
                "impact_trend": self._calculate_impact_trend(symbol_articles),
                "key_articles": [{"title": a.title, "sentiment": a.sentiment_score, "impact": a.impact_score} 
                               for a in symbol_articles[:5]],
                "agent_analysis": response.get("analysis", {}),
                "price_impact_prediction": response.get("price_impact", "neutral"),
                "trading_recommendations": response.get("recommendations", [])
            }
            
            return impact_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze news impact for {symbol}: {e}")
            return {"error": str(e)}
    
    def _generate_sentiment_analysis_prompt(self, context: Dict[str, Any], text: str) -> str:
        """Generate sentiment analysis prompt."""
        return f"""Analyze the sentiment of the following text and provide insights:

Text: {text[:500]}...

Context:
- Text Length: {context['text_length']} characters
- Symbols: {context['symbols']}
- Context: {context['context']}
- Crypto Keywords: {context['crypto_keywords_present']}

Provide:
1. Sentiment assessment
2. Confidence level
3. Key insights
4. Trading implications
5. Market impact analysis

Respond in JSON format with keys: confidence, insights, trading_implications, market_impact, confidence_multiplier"""

    def _generate_signal_generation_prompt(self, context: Dict[str, Any]) -> str:
        """Generate signal generation prompt."""
        return f"""Generate news-based trading signals for the following context:

Context:
- Symbols: {context['symbols']}
- Timeframe: {context['timeframe']}
- Sentiment Threshold: {context['sentiment_threshold']}
- Impact Threshold: {context['impact_threshold']}
- Available Articles: {context['available_articles']}
- Recent Articles: {context['recent_articles']}

Provide:
1. Signal generation strategy
2. Confidence multiplier
3. Additional reasoning
4. Risk considerations
5. Market conditions assessment

Respond in JSON format with keys: strategy, confidence_multiplier, additional_reasoning, risks, market_conditions"""

    def _generate_sentiment_summary_prompt(self, context: Dict[str, Any]) -> str:
        """Generate sentiment summary prompt."""
        return f"""Analyze the sentiment summary and provide market insights:

Summary:
- Total Articles: {context['total_articles']}
- Time Period: {context['time_period']}
- Sentiment Distribution: {context['sentiment_distribution']}
- Top Keywords: {context['top_keywords']}
- Impact Scores: {context['impact_scores'][:10]}  # First 10

Provide:
1. Market mood assessment
2. Key insights
3. Trading implications
4. Risk factors
5. Future outlook

Respond in JSON format with keys: market_mood, insights, trading_implications, risks, outlook"""

    def _generate_impact_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Generate impact analysis prompt."""
        return f"""Analyze the news impact on {context['symbol']}:

Context:
- Symbol: {context['symbol']}
- Timeframe: {context['timeframe']}
- Articles Count: {context['articles_count']}
- Sentiment Scores: {context['sentiment_scores'][:10]}
- Impact Scores: {context['impact_scores'][:10]}

Provide:
1. Impact analysis
2. Price impact prediction
3. Trading recommendations
4. Risk assessment
5. Market sentiment

Respond in JSON format with keys: analysis, price_impact, recommendations, risks, sentiment"""

    async def _get_agent_response(self, prompt: str) -> Dict[str, Any]:
        """Get response from AutoGen agent."""
        try:
            # This would integrate with the AutoGen agent
            # For now, return a structured response
            return {
                "confidence": 0.85,
                "insights": ["Sentiment analysis completed", "Market conditions stable"],
                "trading_implications": ["Monitor for opportunities", "Consider position sizing"],
                "market_impact": "moderate",
                "confidence_multiplier": 1.0,
                "additional_reasoning": "Based on comprehensive analysis",
                "market_mood": "neutral",
                "price_impact": "neutral",
                "recommendations": ["Continue monitoring", "Adjust positions as needed"]
            }
        except Exception as e:
            logger.error(f"Failed to get agent response: {e}")
            return {"error": str(e)}
    
    def _extract_crypto_keywords(self, text: str) -> List[str]:
        """Extract cryptocurrency keywords from text."""
        text_lower = text.lower()
        return [keyword for keyword in self.crypto_keywords if keyword in text_lower]
    
    def _is_crypto_relevant(self, text: str) -> bool:
        """Check if text is relevant to cryptocurrency."""
        crypto_keywords = self._extract_crypto_keywords(text)
        return len(crypto_keywords) > 0
    
    def _generate_trading_signals_from_sentiment(self, sentiment_score: float, impact_score: float,
                                               symbols: List[str], response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trading signals from sentiment analysis."""
        signals = []
        for symbol in symbols:
            if sentiment_score > 0.3 and impact_score > 0.5:
                signal_type = "buy"
            elif sentiment_score < -0.3 and impact_score > 0.5:
                signal_type = "sell"
            else:
                signal_type = "hold"
            
            signals.append({
                "symbol": symbol,
                "signal_type": signal_type,
                "confidence": abs(sentiment_score) * impact_score,
                "reasoning": f"Sentiment: {sentiment_score:.2f}, Impact: {impact_score:.2f}"
            })
        
        return signals
    
    def _calculate_sentiment_distribution(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Calculate sentiment distribution."""
        distribution = {"positive": 0, "neutral": 0, "negative": 0}
        for article in articles:
            if article.sentiment_score > 0.1:
                distribution["positive"] += 1
            elif article.sentiment_score < -0.1:
                distribution["negative"] += 1
            else:
                distribution["neutral"] += 1
        return distribution
    
    def _extract_top_keywords(self, articles: List[NewsArticle]) -> List[str]:
        """Extract top keywords from articles."""
        keyword_counts = {}
        for article in articles:
            for keyword in article.relevant_keywords or []:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Return top 10 keywords
        return sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _calculate_sentiment_trend(self, articles: List[NewsArticle]) -> str:
        """Calculate sentiment trend."""
        if len(articles) < 2:
            return "insufficient_data"
        
        # Sort by time and calculate trend
        sorted_articles = sorted(articles, key=lambda x: x.published_at)
        first_half = sorted_articles[:len(sorted_articles)//2]
        second_half = sorted_articles[len(sorted_articles)//2:]
        
        first_avg = np.mean([a.sentiment_score for a in first_half])
        second_avg = np.mean([a.sentiment_score for a in second_half])
        
        if second_avg > first_avg + 0.1:
            return "improving"
        elif second_avg < first_avg - 0.1:
            return "declining"
        else:
            return "stable"
    
    def _calculate_impact_trend(self, articles: List[NewsArticle]) -> str:
        """Calculate impact trend."""
        if len(articles) < 2:
            return "insufficient_data"
        
        # Sort by time and calculate trend
        sorted_articles = sorted(articles, key=lambda x: x.published_at)
        first_half = sorted_articles[:len(sorted_articles)//2]
        second_half = sorted_articles[len(sorted_articles)//2:]
        
        first_avg = np.mean([a.impact_score for a in first_half])
        second_avg = np.mean([a.impact_score for a in second_half])
        
        if second_avg > first_avg + 0.1:
            return "increasing"
        elif second_avg < first_avg - 0.1:
            return "decreasing"
        else:
            return "stable"
    
    async def _store_articles(self, articles: List[NewsArticle]):
        """Store articles in database."""
        try:
            # This would store articles in the database
            # For now, just log the storage
            logger.info(f"Storing {len(articles)} articles in database")
        except Exception as e:
            logger.error(f"Failed to store articles: {e}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        return {
            "agent_type": "agentic_news_sentiment",
            "status": "running",
            "version": "1.0.0",
            "articles_collected": len(self.collected_articles),
            "news_sources": len([url for urls in self.news_sources.values() for url in urls]),
            "last_collection": datetime.utcnow().isoformat(),
            "sentiment_analyzer_active": self.sentiment_analyzer is not None,
            "signal_generator_active": self.signal_generator is not None
        }


class NewsSentimentAnalyzer:
    """Technical sentiment analyzer."""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using multiple methods."""
        try:
            # TextBlob analysis
            blob = TextBlob(text)
            textblob_sentiment = blob.sentiment.polarity
            
            # VADER analysis
            vader_scores = self.vader_analyzer.polarity_scores(text)
            vader_sentiment = vader_scores['compound']
            
            # Combine scores
            combined_sentiment = (textblob_sentiment + vader_sentiment) / 2
            
            # Determine label
            if combined_sentiment > 0.1:
                sentiment_label = "positive"
            elif combined_sentiment < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            # Extract keywords
            keywords = self._extract_keywords(text)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(text, combined_sentiment, keywords)
            
            return {
                'sentiment_score': combined_sentiment,
                'sentiment_label': sentiment_label,
                'textblob_sentiment': textblob_sentiment,
                'vader_sentiment': vader_sentiment,
                'keywords': keywords,
                'impact_score': impact_score,
                'entities': self._extract_entities(text)
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'keywords': [],
                'impact_score': 0.0,
                'entities': []
            }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        # Simple keyword extraction - in production, use more sophisticated NLP
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Filter short words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top keywords
        return sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        # Simple entity extraction - in production, use NER
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(entities))[:10]
    
    def _calculate_impact_score(self, text: str, sentiment_score: float, keywords: List[str]) -> float:
        """Calculate impact score based on various factors."""
        # Base impact on sentiment strength
        impact = abs(sentiment_score)
        
        # Boost impact for important keywords
        important_keywords = ['bitcoin', 'ethereum', 'crypto', 'market', 'price', 'trading']
        keyword_boost = sum(1 for keyword, _ in keywords if keyword in important_keywords)
        impact += keyword_boost * 0.1
        
        # Boost impact for longer texts (more detailed analysis)
        impact += min(len(text) / 1000, 0.2)
        
        return min(impact, 1.0)


class NewsCollector:
    """News collection from various sources."""
    
    def __init__(self):
        self.session = None
    
    async def initialize(self):
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
    
    async def fetch_rss_feed(self, url: str) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feed."""
        try:
            async with self.session.get(url) as response:
                content = await response.text()
                feed = feedparser.parse(content)
                
                articles = []
                for entry in feed.entries[:10]:  # Limit to 10 articles
                    article = {
                        'title': entry.get('title', ''),
                        'content': entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'published_at': self._parse_date(entry.get('published', ''))
                    }
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {url}: {e}")
            return []
    
    async def fetch_reddit_posts(self, subreddit: str) -> List[Dict[str, Any]]:
        """Fetch posts from Reddit subreddit."""
        try:
            # This would use Reddit API in production
            # For now, return mock data
            return [
                {
                    'title': f'Reddit post from {subreddit}',
                    'content': 'Sample Reddit content',
                    'url': f'https://reddit.com/r/{subreddit}',
                    'published_at': datetime.utcnow()
                }
            ]
        except Exception as e:
            logger.error(f"Failed to fetch Reddit posts from {subreddit}: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        try:
            # Try various date formats
            formats = [
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S%z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S %z'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            return datetime.utcnow()
            
        except Exception as e:
            logger.warning(f"Failed to parse date {date_str}: {e}")
            return datetime.utcnow()


class NewsSignalGenerator:
    """Generate trading signals from news analysis."""
    
    def __init__(self, sentiment_analyzer: NewsSentimentAnalyzer):
        self.sentiment_analyzer = sentiment_analyzer
    
    def generate_signals(self, articles: List[NewsArticle], symbols: List[str], 
                        sentiment_threshold: float = 0.3, impact_threshold: float = 0.5) -> List[NewsSignalResult]:
        """Generate trading signals from news articles."""
        signals = []
        
        for symbol in symbols:
            # Find articles mentioning the symbol
            symbol_articles = [
                article for article in articles
                if symbol.lower() in (article.title + " " + article.content).lower()
            ]
            
            if not symbol_articles:
                continue
            
            # Calculate aggregate sentiment and impact
            sentiment_scores = [article.sentiment_score for article in symbol_articles]
            impact_scores = [article.impact_score for article in symbol_articles]
            
            avg_sentiment = np.mean(sentiment_scores)
            avg_impact = np.mean(impact_scores)
            
            # Generate signal based on thresholds
            if avg_sentiment > sentiment_threshold and avg_impact > impact_threshold:
                signal_type = "buy"
                confidence = min(avg_sentiment * avg_impact, 1.0)
            elif avg_sentiment < -sentiment_threshold and avg_impact > impact_threshold:
                signal_type = "sell"
                confidence = min(abs(avg_sentiment) * avg_impact, 1.0)
            else:
                signal_type = "hold"
                confidence = 0.5
            
            # Generate reasoning
            reasoning = self._generate_reasoning(symbol_articles, avg_sentiment, avg_impact)
            
            # Create signal result
            signal = NewsSignalResult(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                sentiment_score=avg_sentiment,
                impact_score=avg_impact,
                reasoning=reasoning,
                news_articles=[{"title": a.title, "sentiment": a.sentiment_score, "impact": a.impact_score} 
                             for a in symbol_articles[:5]],
                timestamp=datetime.utcnow()
            )
            
            signals.append(signal)
        
        return signals
    
    def _generate_reasoning(self, articles: List[NewsArticle], sentiment: float, impact: float) -> str:
        """Generate reasoning for trading signal."""
        if sentiment > 0.3:
            mood = "positive"
        elif sentiment < -0.3:
            mood = "negative"
        else:
            mood = "neutral"
        
        if impact > 0.7:
            impact_level = "high"
        elif impact > 0.4:
            impact_level = "moderate"
        else:
            impact_level = "low"
        
        return f"News sentiment is {mood} with {impact_level} impact based on {len(articles)} articles" 