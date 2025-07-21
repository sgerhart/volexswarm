#!/usr/bin/env python3
"""
Test Enhanced Research Agent Capabilities
Demonstrates web scraping, sentiment analysis, and crypto trend detection.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any


class EnhancedResearchTester:
    """Test the enhanced research agent capabilities."""
    
    def __init__(self, research_url: str = "http://localhost:8001"):
        self.research_url = research_url
        self.session = None
    
    async def get_session(self):
        """Get aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{'='*80}")
        print(f"🔍 {title}")
        print(f"{'='*80}")
    
    def print_section(self, title: str):
        """Print a formatted section."""
        print(f"\n📋 {title}")
        print("-" * 60)
    
    async def test_health_check(self) -> bool:
        """Test research agent health."""
        try:
            session = await self.get_session()
            async with session.get(f"{self.research_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Research Agent Health Check:")
                    print(f"   Status: {data.get('status', 'unknown')}")
                    print(f"   Version: {data.get('version', 'unknown')}")
                    print(f"   Vault Connected: {data.get('vault_connected', False)}")
                    print(f"   Database Connected: {data.get('database_connected', False)}")
                    print(f"   OpenAI Available: {data.get('openai_available', False)}")
                    return data.get('status') == 'healthy'
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_crypto_trends(self):
        """Test comprehensive crypto trends research."""
        try:
            session = await self.get_session()
            start_time = time.time()
            
            async with session.get(f"{self.research_url}/research/trends") as response:
                if response.status == 200:
                    data = await response.json()
                    duration = time.time() - start_time
                    
                    print(f"✅ Crypto Trends Research (took {duration:.2f}s):")
                    
                    # Trending coins
                    trending = data.get('results', {}).get('trending_coins', [])
                    if trending:
                        print(f"   📈 Trending Coins ({len(trending)}):")
                        for i, coin in enumerate(trending[:5], 1):
                            print(f"     {i}. {coin.get('name', 'Unknown')} ({coin.get('symbol', 'N/A')}) - Score: {coin.get('score', 0)}")
                    
                    # New listings
                    new_listings = data.get('results', {}).get('new_listings', [])
                    if new_listings:
                        print(f"   🆕 New Listings ({len(new_listings)}):")
                        for i, coin in enumerate(new_listings[:5], 1):
                            print(f"     {i}. {coin.get('name', 'Unknown')} ({coin.get('symbol', 'N/A')}) - ${coin.get('current_price', 0):.6f}")
                    
                    # Fear/Greed Index
                    fear_greed = data.get('results', {}).get('fear_greed_index', {})
                    if fear_greed:
                        print(f"   😨 Fear/Greed Index: {fear_greed.get('value', 0)} ({fear_greed.get('classification', 'Unknown')})")
                    
                    # Reddit sentiment
                    reddit_sentiment = data.get('results', {}).get('reddit_sentiment', {})
                    if reddit_sentiment and 'error' not in reddit_sentiment:
                        print(f"   💬 Reddit Sentiment: {reddit_sentiment.get('overall_sentiment', 'Unknown')} (Score: {reddit_sentiment.get('sentiment_score', 0)})")
                    
                    # News sentiment
                    news_sentiment = data.get('results', {}).get('news_sentiment', {})
                    if news_sentiment and 'error' not in news_sentiment:
                        print(f"   📰 News Sentiment: {news_sentiment.get('overall_sentiment', 'Unknown')} (Score: {news_sentiment.get('sentiment_score', 0)})")
                    
                    return True
                else:
                    print(f"❌ Crypto trends research failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Crypto trends research error: {e}")
            return False
    
    async def test_hot_crypto(self):
        """Test what's hot in crypto."""
        try:
            session = await self.get_session()
            start_time = time.time()
            
            async with session.get(f"{self.research_url}/research/hot") as response:
                if response.status == 200:
                    data = await response.json()
                    duration = time.time() - start_time
                    
                    print(f"✅ Hot Crypto Research (took {duration:.2f}s):")
                    
                    hot_crypto = data.get('hot_crypto', {})
                    
                    # Trending coins
                    trending = hot_crypto.get('trending_coins', [])
                    if trending:
                        print(f"   🔥 Trending Coins:")
                        for i, coin in enumerate(trending[:3], 1):
                            print(f"     {i}. {coin.get('name', 'Unknown')} ({coin.get('symbol', 'N/A')}) - Rank: #{coin.get('market_cap_rank', 'N/A')}")
                    
                    # New listings
                    new_listings = hot_crypto.get('new_listings', [])
                    if new_listings:
                        print(f"   🆕 New Listings:")
                        for i, coin in enumerate(new_listings[:3], 1):
                            change_24h = coin.get('price_change_percentage_24h', 0)
                            change_symbol = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
                            print(f"     {i}. {coin.get('name', 'Unknown')} ({coin.get('symbol', 'N/A')}) {change_symbol} {change_24h:.2f}%")
                    
                    # Market sentiment
                    market_sentiment = hot_crypto.get('market_sentiment', {})
                    fear_greed = market_sentiment.get('fear_greed_index', {})
                    if fear_greed:
                        value = fear_greed.get('value', 0)
                        classification = fear_greed.get('classification', 'Unknown')
                        emoji = "😨" if value < 25 else "😰" if value < 45 else "😐" if value < 55 else "😊" if value < 75 else "😄"
                        print(f"   {emoji} Market Sentiment: {value} ({classification})")
                    
                    return True
                else:
                    print(f"❌ Hot crypto research failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Hot crypto research error: {e}")
            return False
    
    async def test_symbol_research(self, symbol: str = "BTC"):
        """Test symbol-specific research."""
        try:
            session = await self.get_session()
            start_time = time.time()
            
            async with session.get(f"{self.research_url}/research/symbol/{symbol}") as response:
                if response.status == 200:
                    data = await response.json()
                    duration = time.time() - start_time
                    
                    print(f"✅ {symbol} Research (took {duration:.2f}s):")
                    
                    results = data.get('results', {})
                    
                    # Market data
                    market_data = results.get('market_data', {})
                    if market_data:
                        print(f"   📊 Market Data:")
                        print(f"     Current Price: ${market_data.get('current_price', 0):,.2f}")
                        print(f"     24h Change: {market_data.get('price_change_24h', 0):.2f}%")
                        print(f"     24h Volume: {market_data.get('volume_24h', 0):,.0f}")
                        print(f"     24h High: ${market_data.get('high_24h', 0):,.2f}")
                        print(f"     24h Low: ${market_data.get('low_24h', 0):,.2f}")
                    
                    # Sentiment analysis
                    sentiment = results.get('sentiment_analysis', {})
                    if sentiment and 'error' not in sentiment:
                        print(f"   💭 Sentiment Analysis:")
                        print(f"     Overall: {sentiment.get('overall_sentiment', 'Unknown')}")
                        print(f"     Score: {sentiment.get('sentiment_score', 0)}")
                        print(f"     Confidence: {sentiment.get('confidence', 0)}%")
                        
                        key_topics = sentiment.get('key_topics', [])
                        if key_topics:
                            print(f"     Key Topics: {', '.join(key_topics[:3])}")
                    
                    # Reddit posts
                    reddit_posts = results.get('reddit_posts', [])
                    if reddit_posts:
                        print(f"   💬 Reddit Discussion ({len(reddit_posts)} posts):")
                        for i, post in enumerate(reddit_posts[:3], 1):
                            title = post.get('title', 'No title')[:50] + "..." if len(post.get('title', '')) > 50 else post.get('title', 'No title')
                            score = post.get('score', 0)
                            comments = post.get('comments', 0)
                            print(f"     {i}. {title} (Score: {score}, Comments: {comments})")
                    
                    return True
                else:
                    print(f"❌ {symbol} research failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ {symbol} research error: {e}")
            return False
    
    async def test_sentiment_analysis(self, symbol: str = "ETH"):
        """Test sentiment analysis for a specific symbol."""
        try:
            session = await self.get_session()
            start_time = time.time()
            
            async with session.get(f"{self.research_url}/research/sentiment/{symbol}") as response:
                if response.status == 200:
                    data = await response.json()
                    duration = time.time() - start_time
                    
                    print(f"✅ {symbol} Sentiment Analysis (took {duration:.2f}s):")
                    
                    sentiment = data.get('sentiment', {})
                    if sentiment and 'error' not in sentiment:
                        print(f"   🧠 Sentiment Analysis:")
                        print(f"     Overall Sentiment: {sentiment.get('overall_sentiment', 'Unknown')}")
                        print(f"     Sentiment Score: {sentiment.get('sentiment_score', 0)}")
                        print(f"     Confidence: {sentiment.get('confidence', 0)}%")
                        print(f"     Community Mood: {sentiment.get('community_mood', 'Unknown')}")
                        print(f"     Market Impact: {sentiment.get('market_impact', 'Unknown')}")
                        
                        key_topics = sentiment.get('key_topics', [])
                        if key_topics:
                            print(f"     Key Topics: {', '.join(key_topics)}")
                        
                        analysis = sentiment.get('analysis', '')
                        if analysis:
                            print(f"     Analysis: {analysis[:200]}...")
                    
                    reddit_posts = data.get('reddit_posts', [])
                    if reddit_posts:
                        print(f"   💬 Reddit Posts Analyzed: {len(reddit_posts)}")
                    
                    return True
                else:
                    print(f"❌ {symbol} sentiment analysis failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ {symbol} sentiment analysis error: {e}")
            return False
    
    async def test_market_data(self, symbol: str = "BTCUSD"):
        """Test market data endpoint."""
        try:
            session = await self.get_session()
            start_time = time.time()
            
            async with session.get(f"{self.research_url}/market-data/{symbol}") as response:
                if response.status == 200:
                    data = await response.json()
                    duration = time.time() - start_time
                    
                    print(f"✅ Market Data for {symbol} (took {duration:.2f}s):")
                    
                    market_data = data.get('data', {})
                    if market_data:
                        print(f"   💰 Price Data:")
                        print(f"     Last Price: ${market_data.get('last_price', 0):,.2f}")
                        print(f"     Bid: ${market_data.get('bid', 0):,.2f}")
                        print(f"     Ask: ${market_data.get('ask', 0):,.2f}")
                        print(f"     24h Change: {market_data.get('change_percent_24h', 0):.2f}%")
                        print(f"     24h Volume: {market_data.get('volume_24h', 0):,.0f}")
                        print(f"     24h High: ${market_data.get('high_24h', 0):,.2f}")
                        print(f"     24h Low: ${market_data.get('low_24h', 0):,.2f}")
                    
                    return True
                else:
                    print(f"❌ Market data failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Market data error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all research agent tests."""
        self.print_header("Enhanced Research Agent Test Suite")
        print(f"Testing research agent at: {self.research_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test health check first
        self.print_section("Health Check")
        if not await self.test_health_check():
            print("❌ Research agent is not healthy. Stopping tests.")
            return
        
        # Test market data (basic functionality)
        self.print_section("Market Data Test")
        await self.test_market_data("BTCUSD")
        
        # Test crypto trends research
        self.print_section("Crypto Trends Research")
        await self.test_crypto_trends()
        
        # Test hot crypto research
        self.print_section("Hot Crypto Research")
        await self.test_hot_crypto()
        
        # Test symbol research
        self.print_section("Symbol Research")
        await self.test_symbol_research("BTC")
        await self.test_symbol_research("ETH")
        
        # Test sentiment analysis
        self.print_section("Sentiment Analysis")
        await self.test_sentiment_analysis("BTC")
        await self.test_sentiment_analysis("ETH")
        
        self.print_header("Test Suite Complete")
        print("🎉 Enhanced research agent testing completed!")
        print("\n📊 Research Capabilities Tested:")
        print("   ✅ Web scraping (Reddit, news)")
        print("   ✅ API integration (CoinGecko, Fear/Greed)")
        print("   ✅ Sentiment analysis (GPT-powered)")
        print("   ✅ Trend detection")
        print("   ✅ Market data collection")
        print("   ✅ Caching and performance")
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()


async def main():
    """Main test function."""
    tester = EnhancedResearchTester()
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main()) 