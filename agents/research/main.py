"""
Enhanced Research Agent for VolexSwarm
Handles comprehensive market research, data collection, sentiment analysis, and trend detection.
"""

import sys
import os
import logging
import asyncio
import aiohttp
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import time
import random

# Add the parent directory to the path to import common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_exchange_credentials, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import PriceData, Strategy, Signal
from common.openai_client import get_openai_client, is_openai_available

# Initialize structured logger
logger = get_logger("research")

app = FastAPI(title="VolexSwarm Enhanced Research Agent", version="2.0.0")

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
openai_client = None

# Research data cache
research_cache = {}
cache_ttl = 300  # 5 minutes


class ResearchTool:
    """Base class for research tools."""
    
    def __init__(self, name: str):
        self.name = name
        self.last_used = None
        self.rate_limit = 1.0  # seconds between requests
    
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the research tool."""
        raise NotImplementedError
    
    def can_execute(self) -> bool:
        """Check if tool can be executed (rate limiting)."""
        if not self.last_used:
            return True
        return (datetime.now() - self.last_used).total_seconds() >= self.rate_limit


class WebScrapingTool(ResearchTool):
    """Tool for web scraping crypto news and data."""
    
    def __init__(self):
        super().__init__("web_scraper")
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def get_session(self):
        """Get aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def scrape_reddit(self, subreddit: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Scrape Reddit posts for sentiment analysis."""
        try:
            session = await self.get_session()
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = []
                    
                    for post in data['data']['children']:
                        post_data = post['data']
                        posts.append({
                            'title': post_data.get('title', ''),
                            'content': post_data.get('selftext', ''),
                            'score': post_data.get('score', 0),
                            'comments': post_data.get('num_comments', 0),
                            'created_utc': post_data.get('created_utc', 0),
                            'url': post_data.get('url', ''),
                            'author': post_data.get('author', ''),
                            'subreddit': subreddit
                        })
                    
                    return posts
                else:
                    logger.warning(f"Failed to scrape Reddit {subreddit}: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error scraping Reddit {subreddit}: {e}")
            return []
    
    async def scrape_crypto_news(self) -> List[Dict[str, Any]]:
        """Scrape crypto news from various sources."""
        try:
            session = await self.get_session()
            news_sources = [
                "https://cointelegraph.com/rss",
                "https://coindesk.com/arc/outboundfeeds/rss/",
                "https://bitcoin.com/news/feed/"
            ]
            
            all_news = []
            
            for source in news_sources:
                try:
                    async with session.get(source) as response:
                        if response.status == 200:
                            content = await response.text()
                            soup = BeautifulSoup(content, 'xml')
                            
                            for item in soup.find_all('item')[:5]:  # Top 5 articles
                                news_item = {
                                    'title': item.find('title').text if item.find('title') else '',
                                    'description': item.find('description').text if item.find('description') else '',
                                    'link': item.find('link').text if item.find('link') else '',
                                    'pubDate': item.find('pubDate').text if item.find('pubDate') else '',
                                    'source': source
                                }
                                all_news.append(news_item)
                                
                except Exception as e:
                    logger.warning(f"Failed to scrape {source}: {e}")
                    continue
            
            return all_news
            
        except Exception as e:
            logger.error(f"Error scraping crypto news: {e}")
            return []
    
    async def execute(self, tool_type: str, **kwargs) -> Dict[str, Any]:
        """Execute web scraping tool."""
        if not self.can_execute():
            return {"error": "Rate limit exceeded"}
        
        self.last_used = datetime.now()
        
        if tool_type == "reddit":
            subreddit = kwargs.get('subreddit', 'cryptocurrency')
            limit = kwargs.get('limit', 10)
            return {"posts": await self.scrape_reddit(subreddit, limit)}
        
        elif tool_type == "news":
            return {"news": await self.scrape_crypto_news()}
        
        else:
            return {"error": f"Unknown tool type: {tool_type}"}


class APITool(ResearchTool):
    """Tool for API-based research data."""
    
    def __init__(self):
        super().__init__("api_tool")
        self.session = None
    
    async def get_session(self):
        """Get aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_trending_coins(self) -> List[Dict[str, Any]]:
        """Get trending coins from CoinGecko."""
        try:
            session = await self.get_session()
            url = "https://api.coingecko.com/api/v3/search/trending"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    trending = []
                    
                    for coin in data.get('coins', []):
                        item = coin.get('item', {})
                        trending.append({
                            'id': item.get('id', ''),
                            'name': item.get('name', ''),
                            'symbol': item.get('symbol', ''),
                            'market_cap_rank': item.get('market_cap_rank', 0),
                            'price_btc': item.get('price_btc', 0),
                            'score': item.get('score', 0)
                        })
                    
                    return trending
                else:
                    logger.warning(f"Failed to get trending coins: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting trending coins: {e}")
            return []
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get crypto fear and greed index."""
        try:
            session = await self.get_session()
            url = "https://api.alternative.me/fng/"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    latest = data.get('data', [{}])[0]
                    
                    return {
                        'value': int(latest.get('value', 0)),
                        'classification': latest.get('value_classification', ''),
                        'timestamp': latest.get('timestamp', ''),
                        'time_until_update': latest.get('time_until_update', '')
                    }
                else:
                    logger.warning(f"Failed to get fear/greed index: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting fear/greed index: {e}")
            return {}
    
    async def get_new_listings(self) -> List[Dict[str, Any]]:
        """Get new coin listings from CoinGecko."""
        try:
            session = await self.get_session()
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'created_desc',
                'per_page': 20,
                'page': 1,
                'sparkline': False
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    new_listings = []
                    
                    for coin in data:
                        new_listings.append({
                            'id': coin.get('id', ''),
                            'name': coin.get('name', ''),
                            'symbol': coin.get('symbol', '').upper(),
                            'current_price': coin.get('current_price', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'volume_24h': coin.get('total_volume', 0),
                            'price_change_24h': coin.get('price_change_24h', 0),
                            'price_change_percentage_24h': coin.get('price_change_percentage_24h', 0),
                            'created_at': coin.get('genesis_date', '')
                        })
                    
                    return new_listings
                else:
                    logger.warning(f"Failed to get new listings: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting new listings: {e}")
            return []
    
    async def execute(self, tool_type: str, **kwargs) -> Dict[str, Any]:
        """Execute API tool."""
        if not self.can_execute():
            return {"error": "Rate limit exceeded"}
        
        self.last_used = datetime.now()
        
        if tool_type == "trending":
            return {"trending": await self.get_trending_coins()}
        
        elif tool_type == "fear_greed":
            return {"fear_greed": await self.get_fear_greed_index()}
        
        elif tool_type == "new_listings":
            return {"new_listings": await self.get_new_listings()}
        
        else:
            return {"error": f"Unknown tool type: {tool_type}"}


class SentimentAnalysisTool(ResearchTool):
    """Tool for sentiment analysis using OpenAI GPT."""
    
    def __init__(self):
        super().__init__("sentiment_analyzer")
        self.openai_client = None
    
    def get_openai_client(self):
        """Get OpenAI client."""
        if not self.openai_client and is_openai_available():
            self.openai_client = get_openai_client()
        return self.openai_client.client if self.openai_client else None
    
    async def analyze_reddit_sentiment(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment of Reddit posts."""
        try:
            client = self.get_openai_client()
            if not client:
                return {"error": "OpenAI client not available"}
            
            # Prepare posts for analysis
            posts_text = []
            for post in posts[:10]:  # Analyze top 10 posts
                text = f"Title: {post.get('title', '')}\nContent: {post.get('content', '')[:500]}"
                posts_text.append(text)
            
            combined_text = "\n\n---\n\n".join(posts_text)
            
            prompt = f"""
            Analyze the sentiment of these Reddit posts about cryptocurrency. 
            Provide a comprehensive analysis including:
            1. Overall sentiment (bullish/bearish/neutral)
            2. Key topics being discussed
            3. Community mood
            4. Potential market impact
            5. Confidence score (0-100)
            
            Posts:
            {combined_text}
            
            Provide your analysis in JSON format:
            {{
                "overall_sentiment": "bullish/bearish/neutral",
                "sentiment_score": -100 to 100,
                "key_topics": ["topic1", "topic2"],
                "community_mood": "description",
                "market_impact": "description",
                "confidence": 0-100,
                "analysis": "detailed analysis"
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                return {"error": "Failed to parse sentiment analysis"}
                
        except Exception as e:
            logger.error(f"Error analyzing Reddit sentiment: {e}")
            return {"error": str(e)}
    
    async def analyze_news_sentiment(self, news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment of crypto news."""
        try:
            client = self.get_openai_client()
            if not client:
                return {"error": "OpenAI client not available"}
            
            # Prepare news for analysis
            news_text = []
            for item in news[:10]:  # Analyze top 10 news items
                text = f"Title: {item.get('title', '')}\nDescription: {item.get('description', '')[:500]}"
                news_text.append(text)
            
            combined_text = "\n\n---\n\n".join(news_text)
            
            prompt = f"""
            Analyze the sentiment of these cryptocurrency news articles. 
            Provide a comprehensive analysis including:
            1. Overall market sentiment from news
            2. Key events and their potential impact
            3. Market-moving news
            4. Risk factors mentioned
            5. Confidence score (0-100)
            
            News Articles:
            {combined_text}
            
            Provide your analysis in JSON format:
            {{
                "overall_sentiment": "bullish/bearish/neutral",
                "sentiment_score": -100 to 100,
                "key_events": ["event1", "event2"],
                "market_impact": "description",
                "risk_factors": ["risk1", "risk2"],
                "confidence": 0-100,
                "analysis": "detailed analysis"
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                return {"error": "Failed to parse news sentiment analysis"}
                
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return {"error": str(e)}
    
    async def execute(self, tool_type: str, **kwargs) -> Dict[str, Any]:
        """Execute sentiment analysis tool."""
        if not self.can_execute():
            return {"error": "Rate limit exceeded"}
        
        self.last_used = datetime.now()
        
        if tool_type == "reddit_sentiment":
            posts = kwargs.get('posts', [])
            return await self.analyze_reddit_sentiment(posts)
        
        elif tool_type == "news_sentiment":
            news = kwargs.get('news', [])
            return await self.analyze_news_sentiment(news)
        
        else:
            return {"error": f"Unknown tool type: {tool_type}"}


class ResearchAgent:
    """Enhanced research agent with tool-based framework."""
    
    def __init__(self):
        self.tools = {
            'web_scraper': WebScrapingTool(),
            'api_tool': APITool(),
            'sentiment_analyzer': SentimentAnalysisTool()
        }
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if still valid."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def cache_data(self, key: str, data: Dict[str, Any]):
        """Cache data with timestamp."""
        self.cache[key] = (data, datetime.now())
    
    async def research_crypto_trends(self) -> Dict[str, Any]:
        """Research current crypto trends and hot topics."""
        try:
            # Check cache first
            cached = self.get_cached_data('crypto_trends')
            if cached:
                return cached
            
            results = {}
            
            # Get trending coins
            api_tool = self.tools['api_tool']
            trending_result = await api_tool.execute('trending')
            results['trending_coins'] = trending_result.get('trending', [])
            
            # Get new listings
            new_listings_result = await api_tool.execute('new_listings')
            results['new_listings'] = new_listings_result.get('new_listings', [])
            
            # Get fear/greed index
            fear_greed_result = await api_tool.execute('fear_greed')
            results['fear_greed_index'] = fear_greed_result.get('fear_greed', {})
            
            # Scrape Reddit for community sentiment
            web_tool = self.tools['web_scraper']
            reddit_result = await web_tool.execute('reddit', subreddit='cryptocurrency', limit=15)
            results['reddit_posts'] = reddit_result.get('posts', [])
            
            # Analyze Reddit sentiment
            sentiment_tool = self.tools['sentiment_analyzer']
            reddit_sentiment = await sentiment_tool.execute('reddit_sentiment', posts=results['reddit_posts'])
            results['reddit_sentiment'] = reddit_sentiment
            
            # Scrape crypto news
            news_result = await web_tool.execute('news')
            results['crypto_news'] = news_result.get('news', [])
            
            # Analyze news sentiment
            news_sentiment = await sentiment_tool.execute('news_sentiment', news=results['crypto_news'])
            results['news_sentiment'] = news_sentiment
            
            # Cache results
            self.cache_data('crypto_trends', results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error researching crypto trends: {e}")
            return {"error": str(e)}
    
    async def research_symbol(self, symbol: str) -> Dict[str, Any]:
        """Research a specific cryptocurrency symbol."""
        try:
            # Check cache first
            cache_key = f'symbol_research_{symbol}'
            cached = self.get_cached_data(cache_key)
            if cached:
                return cached
            
            results = {}
            
            # Get market data
            if db_client:
                session = db_client.get_session()
                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)
                
                price_data = session.query(PriceData).filter(
                    PriceData.symbol == symbol,
                    PriceData.time >= start_time
                ).order_by(PriceData.time.desc()).limit(100).all()
                
                if price_data:
                    results['market_data'] = {
                        'current_price': price_data[0].close,
                        'price_change_24h': ((price_data[0].close - price_data[24].close) / price_data[24].close * 100) if len(price_data) > 24 else 0,
                        'volume_24h': sum([d.volume for d in price_data[:24]]) if len(price_data) >= 24 else 0,
                        'high_24h': max([d.high for d in price_data[:24]]) if len(price_data) >= 24 else price_data[0].high,
                        'low_24h': min([d.low for d in price_data[:24]]) if len(price_data) >= 24 else price_data[0].low
                    }
                
                session.close()
            
            # Scrape Reddit for symbol-specific posts
            web_tool = self.tools['web_scraper']
            reddit_posts = []
            
            # Search in multiple crypto subreddits
            for subreddit in ['cryptocurrency', 'bitcoin', 'ethereum']:
                posts = await web_tool.execute('reddit', subreddit=subreddit, limit=10)
                # Filter posts mentioning the symbol
                symbol_posts = [post for post in posts if symbol.lower() in post.get('title', '').lower() or symbol.lower() in post.get('content', '').lower()]
                reddit_posts.extend(symbol_posts)
            
            results['reddit_posts'] = reddit_posts[:10]  # Top 10 relevant posts
            
            # Analyze sentiment for this symbol
            if reddit_posts:
                sentiment_tool = self.tools['sentiment_analyzer']
                sentiment = await sentiment_tool.execute('reddit_sentiment', posts=reddit_posts)
                results['sentiment_analysis'] = sentiment
            
            # Cache results
            self.cache_data(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error researching symbol {symbol}: {e}")
            return {"error": str(e)}


# Global research agent instance
research_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize the enhanced research agent on startup."""
    global vault_client, db_client, openai_client, research_agent
    
    try:
        with logger.log_operation("agent_startup"):
            # Initialize Vault client
            vault_client = get_vault_client()
            logger.info("Vault client initialized successfully")
            
            # Initialize database client
            db_client = get_db_client()
            logger.info("Database client initialized successfully")
            
            # Initialize OpenAI client
            if is_openai_available():
                openai_client = get_openai_client()
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI client not available")
            
            # Initialize research agent
            research_agent = ResearchAgent()
            logger.info("Enhanced research agent initialized successfully")
            
            # Load agent configuration
            config = get_agent_config("research")
            if config:
                logger.info("Loaded configuration for research agent", config)
            
            logger.info("Enhanced research agent initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize research agent", exception=e)
        raise


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "agent": "enhanced_research",
        "status": "running",
        "version": "2.0.0",
        "vault_connected": vault_client.health_check() if vault_client else False,
        "openai_available": is_openai_available()
    }


@app.get("/health")
def health_check():
    """Detailed health check including all connections."""
    try:
        vault_healthy = vault_client.health_check() if vault_client else False
        db_healthy = db_health_check() if db_client else False
        openai_healthy = is_openai_available()
        
        overall_healthy = vault_healthy and db_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "vault_connected": vault_healthy,
            "database_connected": db_healthy,
            "openai_available": openai_healthy,
            "agent": "enhanced_research",
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error("Health check failed", exception=e)
        return {
            "status": "unhealthy",
            "vault_connected": False,
            "database_connected": False,
            "openai_available": False,
            "error": str(e),
            "agent": "enhanced_research"
        }


@app.get("/research/trends")
async def get_crypto_trends():
    """Get comprehensive crypto trends and hot topics."""
    try:
        if not research_agent:
            raise HTTPException(status_code=500, detail="Research agent not initialized")
        
        with logger.log_operation("research_trends"):
            results = await research_agent.research_crypto_trends()
            
            return {
                "agent": "enhanced_research",
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
    except Exception as e:
        logger.error("Failed to get crypto trends", exception=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/symbol/{symbol}")
async def research_symbol(symbol: str):
    """Research a specific cryptocurrency symbol."""
    try:
        if not research_agent:
            raise HTTPException(status_code=500, detail="Research agent not initialized")
        
        with logger.log_operation("research_symbol", {"symbol": symbol}):
            results = await research_agent.research_symbol(symbol.upper())
            
            return {
                "agent": "enhanced_research",
                "symbol": symbol.upper(),
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
    except Exception as e:
        logger.error(f"Failed to research symbol {symbol}", exception=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/hot")
async def get_hot_crypto():
    """Get what's hot in crypto - trending coins, new listings, etc."""
    try:
        if not research_agent:
            raise HTTPException(status_code=500, detail="Research agent not initialized")
        
        with logger.log_operation("research_hot_crypto"):
            # Get trending data
            api_tool = research_agent.tools['api_tool']
            
            trending_result = await api_tool.execute('trending')
            new_listings_result = await api_tool.execute('new_listings')
            fear_greed_result = await api_tool.execute('fear_greed')
            
            # Get Reddit sentiment
            web_tool = research_agent.tools['web_scraper']
            reddit_result = await web_tool.execute('reddit', subreddit='cryptocurrency', limit=10)
            
            sentiment_tool = research_agent.tools['sentiment_analyzer']
            sentiment = await sentiment_tool.execute('reddit_sentiment', posts=reddit_result.get('posts', []))
            
            return {
                "agent": "enhanced_research",
                "timestamp": datetime.now().isoformat(),
                "hot_crypto": {
                    "trending_coins": trending_result.get('trending', []),
                    "new_listings": new_listings_result.get('new_listings', []),
                    "market_sentiment": {
                        "fear_greed_index": fear_greed_result.get('fear_greed', {}),
                        "reddit_sentiment": sentiment
                    },
                    "community_discussion": reddit_result.get('posts', [])
                }
            }
    except Exception as e:
        logger.error("Failed to get hot crypto data", exception=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/sentiment/{symbol}")
async def get_symbol_sentiment(symbol: str):
    """Get sentiment analysis for a specific symbol."""
    try:
        if not research_agent:
            raise HTTPException(status_code=500, detail="Research agent not initialized")
        
        with logger.log_operation("research_sentiment", {"symbol": symbol}):
            # Get symbol research
            symbol_data = await research_agent.research_symbol(symbol.upper())
            
            return {
                "agent": "enhanced_research",
                "symbol": symbol.upper(),
                "timestamp": datetime.now().isoformat(),
                "sentiment": symbol_data.get('sentiment_analysis', {}),
                "reddit_posts": symbol_data.get('reddit_posts', [])
            }
    except Exception as e:
        logger.error(f"Failed to get sentiment for {symbol}", exception=e)
        raise HTTPException(status_code=500, detail=str(e))


# Keep existing endpoints for backward compatibility
@app.get("/market-data/{symbol}")
def get_market_data(symbol: str = "BTCUSD"):
    """Get market data for a specific symbol (public endpoint)."""
    try:
        with logger.log_operation("fetch_market_data", {"symbol": symbol}):
            import ccxt
            
            # Use Binance.US public endpoint
            exchange = ccxt.binanceus({
                'enableRateLimit': True
            })
            
            ticker = exchange.fetch_ticker(symbol)
            
            # Store in database
            if db_client:
                try:
                    session = db_client.get_session()
                    
                    # Use current time instead of ticker timestamp to avoid duplicates
                    current_time = datetime.now()
                    
                    # Check if data already exists for this symbol in the last minute
                    existing_data = session.query(PriceData).filter(
                        PriceData.symbol == symbol,
                        PriceData.time >= current_time - timedelta(minutes=1)
                    ).first()
                    
                    if not existing_data:
                        price_data = PriceData(
                            time=current_time,
                            symbol=symbol,
                            exchange="binanceus",
                            open=ticker.get('open'),
                            high=ticker.get('high'),
                            low=ticker.get('low'),
                            close=ticker.get('last'),
                            volume=ticker.get('baseVolume'),
                            timeframe="1m"
                        )
                        session.add(price_data)
                        session.commit()
                        logger.info("Market data stored in database", {"symbol": symbol})
                    else:
                        logger.debug(f"Market data already exists for {symbol} in the last minute")
                    
                    session.close()
                except Exception as db_error:
                    logger.warning("Failed to store market data in database", {"error": str(db_error)})
            
            return {
                "agent": "enhanced_research",
                "symbol": symbol,
                "data": {
                    "last_price": ticker['last'],
                    "bid": ticker['bid'],
                    "ask": ticker['ask'],
                    "volume_24h": ticker['baseVolume'],
                    "change_24h": ticker['change'],
                    "change_percent_24h": ticker['percentage'],
                    "high_24h": ticker['high'],
                    "low_24h": ticker['low'],
                    "timestamp": ticker['timestamp']
                }
            }
    except Exception as e:
        logger.error("Failed to get market data", {"symbol": symbol, "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
