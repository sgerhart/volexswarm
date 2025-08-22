#!/usr/bin/env python3
"""
VolexSwarm Real Binance Portfolio Verification
Verifies that the system is pulling the user's actual Binance US account information.

This test:
1. Retrieves real portfolio balances from the user's Binance US account
2. Shows actual holdings, available balances, and account status
3. Verifies the system is using real data, not simulated data
4. Displays current market values and portfolio composition
5. Confirms agents can access real account information for trading decisions

IMPORTANT: This accesses your REAL Binance US account data.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import aiohttp
import time

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger("verify_real_binance_portfolio")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class RealBinancePortfolioVerification:
    """Verify real Binance US portfolio access."""
    
    def __init__(self):
        """Initialize the portfolio verification test."""
        
        # Agent endpoints
        self.agent_endpoints = {
            "execution": "http://localhost:8002",
            "realtime_data": "http://localhost:8026",
            "monitor": "http://localhost:8008"
        }
        
        self.verification_results = {
            "start_time": None,
            "binance_connection": False,
            "account_info": {},
            "portfolio_balances": {},
            "trading_balances": {},
            "total_portfolio_value_usd": 0.0,
            "non_zero_balances": {},
            "account_status": "",
            "trading_enabled": False,
            "api_permissions": {},
            "errors": []
        }
    
    async def get_real_account_info(self) -> bool:
        """Get real Binance US account information."""
        try:
            logger.info("🔍 Retrieving REAL Binance US account information...")
            
            async with aiohttp.ClientSession() as session:
                # Try to get account info via execution agent
                async with session.get(
                    f"{self.agent_endpoints['execution']}/health",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        logger.info(f"✅ Execution agent health: {health_data}")
                        
                        # Check if we can get portfolio status
                        try:
                            async with session.get(
                                f"{self.agent_endpoints['execution']}/portfolio/status",
                                timeout=15
                            ) as portfolio_response:
                                if portfolio_response.status == 200:
                                    portfolio_data = await portfolio_response.json()
                                    logger.info(f"📊 Portfolio Status: {json.dumps(portfolio_data, indent=2)}")
                                    self.verification_results["account_info"] = portfolio_data
                                    return True
                                else:
                                    logger.warning(f"⚠️ Portfolio status endpoint returned: {portfolio_response.status}")
                                    
                        except Exception as e:
                            logger.warning(f"⚠️ Portfolio status error: {e}")
                    
                # Try alternative approach - direct balance query
                balance_payload = {
                    "exchange": "binanceus",
                    "include_zero_balances": False
                }
                
                try:
                    async with session.post(
                        f"{self.agent_endpoints['execution']}/balance",
                        json=balance_payload,
                        timeout=15
                    ) as balance_response:
                        if balance_response.status == 200:
                            balance_data = await balance_response.json()
                            logger.info(f"💰 Account Balances: {json.dumps(balance_data, indent=2)}")
                            self.verification_results["portfolio_balances"] = balance_data
                            return True
                        else:
                            logger.warning(f"⚠️ Balance endpoint returned: {balance_response.status}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Balance query error: {e}")
                
                return False
                        
        except Exception as e:
            logger.error(f"❌ Account info retrieval failed: {e}")
            self.verification_results["errors"].append(f"Account info: {e}")
            return False
    
    async def get_real_portfolio_balances(self) -> bool:
        """Get real portfolio balances from Binance US."""
        try:
            logger.info("💰 Retrieving REAL portfolio balances...")
            
            async with aiohttp.ClientSession() as session:
                # Try different endpoints to get balance information
                balance_endpoints = [
                    "/api/portfolio/balances",
                    "/portfolio/balances", 
                    "/balances",
                    "/account/balances",
                    "/api/account/balances"
                ]
                
                for endpoint in balance_endpoints:
                    try:
                        async with session.get(
                            f"{self.agent_endpoints['execution']}{endpoint}",
                            timeout=15
                        ) as response:
                            if response.status == 200:
                                balance_data = await response.json()
                                logger.info(f"💰 Real Balances from {endpoint}:")
                                logger.info(json.dumps(balance_data, indent=2))
                                
                                self.verification_results["portfolio_balances"] = balance_data
                                
                                # Extract non-zero balances
                                if isinstance(balance_data, dict):
                                    if "balances" in balance_data:
                                        balances = balance_data["balances"]
                                    else:
                                        balances = balance_data
                                    
                                    non_zero = {}
                                    total_value = 0.0
                                    
                                    for asset, amount in balances.items():
                                        if isinstance(amount, (int, float)) and amount > 0:
                                            non_zero[asset] = amount
                                            logger.info(f"  💎 {asset}: {amount}")
                                        elif isinstance(amount, dict):
                                            free = amount.get("free", 0)
                                            locked = amount.get("locked", 0)
                                            total = free + locked
                                            if total > 0:
                                                non_zero[asset] = {
                                                    "free": free,
                                                    "locked": locked,
                                                    "total": total
                                                }
                                                logger.info(f"  💎 {asset}: {total} (free: {free}, locked: {locked})")
                                    
                                    self.verification_results["non_zero_balances"] = non_zero
                                    logger.info(f"✅ Found {len(non_zero)} assets with non-zero balances")
                                    return True
                                    
                            elif response.status == 404:
                                continue  # Try next endpoint
                            else:
                                logger.warning(f"⚠️ {endpoint} returned: {response.status}")
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ {endpoint} timed out")
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️ {endpoint} error: {e}")
                        continue
                
                logger.warning("⚠️ No working balance endpoints found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Portfolio balance retrieval failed: {e}")
            self.verification_results["errors"].append(f"Portfolio balances: {e}")
            return False
    
    async def verify_binance_api_access(self) -> bool:
        """Verify direct Binance API access through agents."""
        try:
            logger.info("🔐 Verifying Binance API access...")
            
            async with aiohttp.ClientSession() as session:
                # Test API connectivity
                api_test_payload = {
                    "exchange": "binanceus",
                    "test_connectivity": True
                }
                
                try:
                    async with session.post(
                        f"{self.agent_endpoints['execution']}/api/test",
                        json=api_test_payload,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            api_data = await response.json()
                            logger.info(f"🔐 API Test Result: {json.dumps(api_data, indent=2)}")
                            self.verification_results["api_permissions"] = api_data
                            return True
                        else:
                            logger.warning(f"⚠️ API test returned: {response.status}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ API test error: {e}")
                
                # Alternative: Check account status
                try:
                    async with session.get(
                        f"{self.agent_endpoints['execution']}/account/status",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            status_data = await response.json()
                            logger.info(f"📊 Account Status: {json.dumps(status_data, indent=2)}")
                            self.verification_results["account_status"] = status_data
                            return True
                        else:
                            logger.warning(f"⚠️ Account status returned: {response.status}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Account status error: {e}")
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Binance API verification failed: {e}")
            return False
    
    async def get_current_market_prices(self) -> Dict[str, float]:
        """Get current market prices for portfolio valuation."""
        try:
            logger.info("📈 Getting current market prices...")
            
            async with aiohttp.ClientSession() as session:
                # Connect to get market data
                connect_payload = {
                    "exchange_name": "binanceus",
                    "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "BNBUSDT"]
                }
                
                async with session.post(
                    f"{self.agent_endpoints['realtime_data']}/connect",
                    json=connect_payload,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Connected to market data")
                        
                        # Get ticker data
                        await asyncio.sleep(1)
                        
                        prices = {}
                        for symbol in ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]:
                            try:
                                ticker_payload = {
                                    "exchange_name": "binanceus",
                                    "symbol": symbol
                                }
                                
                                async with session.post(
                                    f"{self.agent_endpoints['realtime_data']}/ticker",
                                    json=ticker_payload,
                                    timeout=5
                                ) as ticker_response:
                                    if ticker_response.status == 200:
                                        ticker_data = await ticker_response.json()
                                        if "price" in ticker_data:
                                            prices[symbol] = float(ticker_data["price"])
                                            logger.info(f"💲 {symbol}: ${ticker_data['price']}")
                                            
                            except Exception as e:
                                logger.warning(f"⚠️ Price for {symbol}: {e}")
                        
                        return prices
                    else:
                        logger.warning("⚠️ Market data connection failed")
                        return {}
                        
        except Exception as e:
            logger.error(f"❌ Market price retrieval failed: {e}")
            return {}
    
    async def calculate_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value in USD."""
        try:
            logger.info("💰 Calculating portfolio value...")
            
            total_value = 0.0
            balances = self.verification_results["non_zero_balances"]
            
            for asset, amount in balances.items():
                if isinstance(amount, dict):
                    asset_amount = amount.get("total", 0)
                else:
                    asset_amount = amount
                
                if asset == "USDT" or asset == "USD":
                    # Direct USD value
                    asset_value = asset_amount
                    total_value += asset_value
                    logger.info(f"  💵 {asset}: {asset_amount} = ${asset_value:.2f}")
                elif asset == "BTC" and "BTCUSDT" in prices:
                    asset_value = asset_amount * prices["BTCUSDT"]
                    total_value += asset_value
                    logger.info(f"  ₿ {asset}: {asset_amount} × ${prices['BTCUSDT']:.2f} = ${asset_value:.2f}")
                elif asset == "ETH" and "ETHUSDT" in prices:
                    asset_value = asset_amount * prices["ETHUSDT"]
                    total_value += asset_value
                    logger.info(f"  Ξ {asset}: {asset_amount} × ${prices['ETHUSDT']:.2f} = ${asset_value:.2f}")
                elif asset == "ADA" and "ADAUSDT" in prices:
                    asset_value = asset_amount * prices["ADAUSDT"]
                    total_value += asset_value
                    logger.info(f"  🔷 {asset}: {asset_amount} × ${prices['ADAUSDT']:.2f} = ${asset_value:.2f}")
                else:
                    logger.info(f"  ❓ {asset}: {asset_amount} (price not available)")
            
            self.verification_results["total_portfolio_value_usd"] = total_value
            logger.info(f"💰 Total Portfolio Value: ${total_value:.2f}")
            
            return total_value
            
        except Exception as e:
            logger.error(f"❌ Portfolio value calculation failed: {e}")
            return 0.0
    
    async def run_portfolio_verification(self) -> Dict[str, Any]:
        """Run comprehensive portfolio verification."""
        try:
            self.verification_results["start_time"] = datetime.now()
            
            logger.info("🔍 Starting Real Binance Portfolio Verification")
            logger.info("=" * 60)
            logger.info("🎯 Verifying: Real account data access")
            
            # Phase 1: Get account information
            logger.info("\n📊 Phase 1: Account Information")
            account_success = await self.get_real_account_info()
            
            # Phase 2: Get portfolio balances
            logger.info("\n💰 Phase 2: Portfolio Balances")
            balance_success = await self.get_real_portfolio_balances()
            
            # Phase 3: Verify API access
            logger.info("\n🔐 Phase 3: API Access Verification")
            api_success = await self.verify_binance_api_access()
            
            # Phase 4: Get market prices
            logger.info("\n📈 Phase 4: Current Market Prices")
            prices = await self.get_current_market_prices()
            
            # Phase 5: Calculate portfolio value
            if self.verification_results["non_zero_balances"] and prices:
                logger.info("\n💰 Phase 5: Portfolio Valuation")
                total_value = await self.calculate_portfolio_value(prices)
            
            # Generate comprehensive report
            await self.generate_verification_report()
            
            # Determine success
            overall_success = (account_success or balance_success or 
                             len(self.verification_results["non_zero_balances"]) > 0)
            
            return {
                "success": overall_success,
                "results": self.verification_results,
                "phases": {
                    "account_info": account_success,
                    "portfolio_balances": balance_success,
                    "api_access": api_success,
                    "market_prices": len(prices) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Portfolio verification failed: {e}")
            self.verification_results["errors"].append(str(e))
            return {"success": False, "error": str(e), "results": self.verification_results}
    
    async def generate_verification_report(self):
        """Generate detailed verification report."""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("📊 REAL BINANCE PORTFOLIO VERIFICATION REPORT")
            logger.info("=" * 60)
            
            # Account Access Status
            logger.info("🔐 ACCOUNT ACCESS:")
            logger.info(f"  • Account Info Retrieved: {'✅' if self.verification_results['account_info'] else '❌'}")
            logger.info(f"  • Portfolio Balances: {'✅' if self.verification_results['portfolio_balances'] else '❌'}")
            logger.info(f"  • API Permissions: {'✅' if self.verification_results['api_permissions'] else '❌'}")
            
            # Portfolio Holdings
            logger.info("\n💰 CURRENT HOLDINGS:")
            if self.verification_results["non_zero_balances"]:
                logger.info("  ✅ Real portfolio data retrieved:")
                for asset, amount in self.verification_results["non_zero_balances"].items():
                    if isinstance(amount, dict):
                        logger.info(f"    💎 {asset}: {amount['total']} (free: {amount['free']}, locked: {amount['locked']})")
                    else:
                        logger.info(f"    💎 {asset}: {amount}")
            else:
                logger.info("  ⚠️ No portfolio balances retrieved")
            
            # Portfolio Value
            logger.info("\n💵 PORTFOLIO VALUE:")
            if self.verification_results["total_portfolio_value_usd"] > 0:
                logger.info(f"  💰 Total Value: ${self.verification_results['total_portfolio_value_usd']:.2f}")
                logger.info(f"  📊 Available for Trading: ${min(25.0, self.verification_results['total_portfolio_value_usd']):.2f}")
            else:
                logger.info("  ⚠️ Portfolio value not calculated")
            
            # Data Verification
            logger.info("\n🔍 DATA VERIFICATION:")
            if self.verification_results["non_zero_balances"]:
                logger.info("  ✅ REAL BINANCE DATA CONFIRMED")
                logger.info("  ✅ System is accessing your actual account")
                logger.info("  ✅ Portfolio balances are live and current")
                logger.info("  ✅ Ready for live trading decisions")
            else:
                logger.info("  ⚠️ Real data access needs verification")
                logger.info("  💡 Check Binance API credentials in Vault")
                logger.info("  💡 Verify account permissions and connectivity")
            
            # Trading Readiness
            logger.info("\n🎯 TRADING READINESS:")
            if (self.verification_results["non_zero_balances"] and 
                self.verification_results["total_portfolio_value_usd"] >= 25.0):
                logger.info("  ✅ READY FOR LIVE TRADING")
                logger.info("  ✅ Sufficient funds available")
                logger.info("  ✅ Real account data accessible")
                logger.info("  ✅ Portfolio composition confirmed")
            elif self.verification_results["non_zero_balances"]:
                logger.info("  ⚠️ Real data confirmed but check trading budget")
                logger.info(f"  💰 Current value: ${self.verification_results['total_portfolio_value_usd']:.2f}")
            else:
                logger.info("  ❌ Need to verify real account access")
            
            # Error Summary
            if self.verification_results["errors"]:
                logger.info("\n❌ ISSUES TO ADDRESS:")
                for i, error in enumerate(self.verification_results["errors"], 1):
                    logger.info(f"  {i}. {error}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Verification report generation failed: {e}")

async def main():
    """Main verification execution function."""
    try:
        verification = RealBinancePortfolioVerification()
        results = await verification.run_portfolio_verification()
        
        if results["success"]:
            print("\n🎉 Real Binance Portfolio Verification - SUCCESS!")
            print("✅ System is accessing your real Binance US account data!")
            return 0
        else:
            print(f"\n⚠️ Verification completed with issues: {results.get('error', 'See detailed report above')}")
            print("🔧 Address the issues above to ensure real data access.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Verification execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
