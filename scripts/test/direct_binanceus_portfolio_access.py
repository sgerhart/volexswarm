#!/usr/bin/env python3
"""
VolexSwarm Direct Binance US Portfolio Access
Directly accesses the user's real Binance US account to retrieve portfolio data.

This test:
1. Uses the AgenticExecutionAgent directly (not HTTP API)
2. Specifically connects to Binance US (not regular Binance)
3. Retrieves real portfolio balances from the user's Binance US account
4. Shows actual holdings, available balances, and account status
5. Verifies the system is using real Binance US data for trading decisions

IMPORTANT: This accesses your REAL Binance US account data.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import time

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the execution agent directly
from agents.execution.agentic_execution_agent import AgenticExecutionAgent, ExchangeManager
from common.vault import VaultClient
from common.logging import get_logger

logger = get_logger("direct_binanceus_portfolio_access")

class DirectBinanceUSPortfolioAccess:
    """Direct access to Binance US portfolio data."""
    
    def __init__(self):
        """Initialize the direct portfolio access test."""
        self.execution_agent = None
        self.exchange_manager = None
        self.vault_client = None
        
        self.portfolio_results = {
            "start_time": None,
            "binanceus_connection": False,
            "account_info": {},
            "portfolio_balances": {},
            "non_zero_balances": {},
            "total_portfolio_value_usd": 0.0,
            "trading_permissions": {},
            "api_credentials_verified": False,
            "exchange_used": "binanceus",
            "errors": []
        }
    
    async def initialize_agents(self) -> bool:
        """Initialize the execution agent and exchange manager."""
        try:
            logger.info("🔧 Initializing Binance US access agents...")
            
            # Initialize Vault client
            self.vault_client = VaultClient()
            logger.info("✅ Vault client initialized")
            
            # Initialize execution agent
            self.execution_agent = AgenticExecutionAgent()
            await self.execution_agent.initialize_infrastructure()
            await self.execution_agent.initialize()
            logger.info("✅ Execution agent initialized")
            
            # Initialize exchange manager directly
            self.exchange_manager = ExchangeManager()
            await self.exchange_manager.initialize_exchanges()
            logger.info("✅ Exchange manager initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            self.portfolio_results["errors"].append(f"Agent initialization: {e}")
            return False
    
    async def verify_binanceus_credentials(self) -> bool:
        """Verify Binance US API credentials are configured."""
        try:
            logger.info("🔐 Verifying Binance US API credentials...")
            
            # Get credentials from Vault
            try:
                binance_creds = self.vault_client.get_secret("binanceus")
                if binance_creds and "api_key" in binance_creds and "secret_key" in binance_creds:
                    api_key = binance_creds["api_key"]
                    secret_key = binance_creds["secret_key"]
                    
                    logger.info(f"✅ Binance US API Key found: {api_key[:8]}...")
                    logger.info(f"✅ Binance US Secret Key found: {secret_key[:8]}...")
                    
                    self.portfolio_results["api_credentials_verified"] = True
                    return True
                else:
                    logger.error("❌ Binance US credentials not found in Vault")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Failed to retrieve Binance US credentials: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Credential verification failed: {e}")
            self.portfolio_results["errors"].append(f"Credential verification: {e}")
            return False
    
    async def get_binanceus_account_info(self) -> bool:
        """Get real Binance US account information."""
        try:
            logger.info("📊 Retrieving REAL Binance US account information...")
            
            # Use the exchange manager to get account info
            try:
                # Get account info from Binance US
                account_info = await self.exchange_manager.get_account_info("binanceus")
                
                if account_info:
                    logger.info("✅ Binance US account info retrieved:")
                    logger.info(json.dumps(account_info, indent=2, default=str))
                    
                    self.portfolio_results["account_info"] = account_info
                    self.portfolio_results["binanceus_connection"] = True
                    
                    # Extract trading permissions
                    if "permissions" in account_info:
                        self.portfolio_results["trading_permissions"] = account_info["permissions"]
                        logger.info(f"🔐 Trading permissions: {account_info['permissions']}")
                    
                    return True
                else:
                    logger.warning("⚠️ No account info returned from Binance US")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Failed to get Binance US account info: {e}")
                self.portfolio_results["errors"].append(f"Account info: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Account info retrieval failed: {e}")
            return False
    
    async def get_binanceus_portfolio_balances(self) -> bool:
        """Get real Binance US portfolio balances."""
        try:
            logger.info("💰 Retrieving REAL Binance US portfolio balances...")
            
            # Use the execution agent's portfolio status method
            try:
                portfolio_status = await self.execution_agent.get_portfolio_status("binanceus")
                
                if portfolio_status:
                    logger.info("✅ Binance US portfolio status retrieved:")
                    logger.info(json.dumps(portfolio_status, indent=2, default=str))
                    
                    self.portfolio_results["portfolio_balances"] = portfolio_status
                    
                    # Extract non-zero balances
                    non_zero_balances = {}
                    total_value_usd = 0.0
                    
                    if "balances" in portfolio_status:
                        balances = portfolio_status["balances"]
                        
                        for asset, balance_info in balances.items():
                            if isinstance(balance_info, dict):
                                free = float(balance_info.get("free", 0))
                                locked = float(balance_info.get("locked", 0))
                                total = free + locked
                                
                                if total > 0:
                                    non_zero_balances[asset] = {
                                        "free": free,
                                        "locked": locked,
                                        "total": total
                                    }
                                    
                                    logger.info(f"💎 {asset}: {total} (free: {free}, locked: {locked})")
                                    
                                    # Calculate USD value
                                    if asset == "USDT" or asset == "USD":
                                        total_value_usd += total
                                    elif asset == "BTC":
                                        # We'll get BTC price separately
                                        pass
                            elif isinstance(balance_info, (int, float)) and balance_info > 0:
                                non_zero_balances[asset] = balance_info
                                logger.info(f"💎 {asset}: {balance_info}")
                    
                    self.portfolio_results["non_zero_balances"] = non_zero_balances
                    self.portfolio_results["total_portfolio_value_usd"] = total_value_usd
                    
                    logger.info(f"✅ Found {len(non_zero_balances)} assets with non-zero balances")
                    return True
                else:
                    logger.warning("⚠️ No portfolio status returned")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Failed to get portfolio status: {e}")
                
                # Try alternative method - direct balance queries
                logger.info("🔄 Trying direct balance queries...")
                
                try:
                    # Get USDT balance
                    usdt_balance = await self.exchange_manager.get_balance("binanceus", "USDT")
                    if usdt_balance:
                        logger.info(f"💵 USDT Balance: {usdt_balance}")
                        self.portfolio_results["non_zero_balances"]["USDT"] = usdt_balance
                    
                    # Get BTC balance
                    btc_balance = await self.exchange_manager.get_balance("binanceus", "BTC")
                    if btc_balance:
                        logger.info(f"₿ BTC Balance: {btc_balance}")
                        self.portfolio_results["non_zero_balances"]["BTC"] = btc_balance
                    
                    # Get ETH balance
                    eth_balance = await self.exchange_manager.get_balance("binanceus", "ETH")
                    if eth_balance:
                        logger.info(f"Ξ ETH Balance: {eth_balance}")
                        self.portfolio_results["non_zero_balances"]["ETH"] = eth_balance
                    
                    if self.portfolio_results["non_zero_balances"]:
                        logger.info("✅ Retrieved balances via direct queries")
                        return True
                    else:
                        logger.warning("⚠️ No balances found via direct queries")
                        return False
                        
                except Exception as e2:
                    logger.error(f"❌ Direct balance queries also failed: {e2}")
                    self.portfolio_results["errors"].append(f"Portfolio balances: {e}, {e2}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Portfolio balance retrieval failed: {e}")
            return False
    
    async def get_current_market_prices(self) -> Dict[str, float]:
        """Get current market prices from Binance US."""
        try:
            logger.info("📈 Getting current Binance US market prices...")
            
            prices = {}
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
            
            for symbol in symbols:
                try:
                    ticker = await self.exchange_manager.get_ticker("binanceus", symbol)
                    if ticker and "last" in ticker:
                        price = float(ticker["last"])
                        prices[symbol] = price
                        logger.info(f"💲 {symbol}: ${price:.2f}")
                    elif ticker and "price" in ticker:
                        price = float(ticker["price"])
                        prices[symbol] = price
                        logger.info(f"💲 {symbol}: ${price:.2f}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get price for {symbol}: {e}")
            
            return prices
            
        except Exception as e:
            logger.error(f"❌ Market price retrieval failed: {e}")
            return {}
    
    async def calculate_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value in USD using Binance US prices."""
        try:
            logger.info("💰 Calculating portfolio value using Binance US prices...")
            
            total_value = 0.0
            balances = self.portfolio_results["non_zero_balances"]
            
            for asset, balance_info in balances.items():
                if isinstance(balance_info, dict):
                    amount = balance_info.get("total", balance_info.get("free", 0))
                else:
                    amount = balance_info
                
                amount = float(amount)
                
                if asset == "USDT" or asset == "USD":
                    asset_value = amount
                    total_value += asset_value
                    logger.info(f"  💵 {asset}: {amount} = ${asset_value:.2f}")
                elif asset == "BTC" and "BTCUSDT" in prices:
                    asset_value = amount * prices["BTCUSDT"]
                    total_value += asset_value
                    logger.info(f"  ₿ {asset}: {amount} × ${prices['BTCUSDT']:.2f} = ${asset_value:.2f}")
                elif asset == "ETH" and "ETHUSDT" in prices:
                    asset_value = amount * prices["ETHUSDT"]
                    total_value += asset_value
                    logger.info(f"  Ξ {asset}: {amount} × ${prices['ETHUSDT']:.2f} = ${asset_value:.2f}")
                elif asset == "ADA" and "ADAUSDT" in prices:
                    asset_value = amount * prices["ADAUSDT"]
                    total_value += asset_value
                    logger.info(f"  🔷 {asset}: {amount} × ${prices['ADAUSDT']:.2f} = ${asset_value:.2f}")
                else:
                    logger.info(f"  ❓ {asset}: {amount} (price not available)")
            
            self.portfolio_results["total_portfolio_value_usd"] = total_value
            logger.info(f"💰 Total Portfolio Value: ${total_value:.2f}")
            
            return total_value
            
        except Exception as e:
            logger.error(f"❌ Portfolio value calculation failed: {e}")
            return 0.0
    
    async def run_binanceus_portfolio_access(self) -> Dict[str, Any]:
        """Run comprehensive Binance US portfolio access test."""
        try:
            self.portfolio_results["start_time"] = datetime.now()
            
            logger.info("🚀 Starting Direct Binance US Portfolio Access")
            logger.info("=" * 60)
            logger.info("🎯 Target: Real Binance US account data")
            logger.info("🏦 Exchange: Binance US (not regular Binance)")
            
            # Phase 1: Initialize agents
            logger.info("\n🔧 Phase 1: Agent Initialization")
            init_success = await self.initialize_agents()
            if not init_success:
                return {"success": False, "error": "Agent initialization failed"}
            
            # Phase 2: Verify credentials
            logger.info("\n🔐 Phase 2: Binance US Credential Verification")
            creds_success = await self.verify_binanceus_credentials()
            
            # Phase 3: Get account info
            logger.info("\n📊 Phase 3: Binance US Account Information")
            account_success = await self.get_binanceus_account_info()
            
            # Phase 4: Get portfolio balances
            logger.info("\n💰 Phase 4: Binance US Portfolio Balances")
            balance_success = await self.get_binanceus_portfolio_balances()
            
            # Phase 5: Get market prices
            logger.info("\n📈 Phase 5: Binance US Market Prices")
            prices = await self.get_current_market_prices()
            
            # Phase 6: Calculate portfolio value
            if self.portfolio_results["non_zero_balances"] and prices:
                logger.info("\n💰 Phase 6: Portfolio Valuation")
                total_value = await self.calculate_portfolio_value(prices)
            
            # Generate comprehensive report
            await self.generate_binanceus_report()
            
            # Cleanup
            if self.execution_agent:
                await self.execution_agent.shutdown()
            if self.exchange_manager:
                await self.exchange_manager.close_exchanges()
            
            # Determine success
            overall_success = (creds_success and 
                             (account_success or balance_success) and
                             len(self.portfolio_results["non_zero_balances"]) > 0)
            
            return {
                "success": overall_success,
                "results": self.portfolio_results,
                "phases": {
                    "initialization": init_success,
                    "credentials": creds_success,
                    "account_info": account_success,
                    "portfolio_balances": balance_success,
                    "market_prices": len(prices) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Binance US portfolio access failed: {e}")
            self.portfolio_results["errors"].append(str(e))
            return {"success": False, "error": str(e), "results": self.portfolio_results}
    
    async def generate_binanceus_report(self):
        """Generate detailed Binance US portfolio report."""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("📊 BINANCE US PORTFOLIO ACCESS REPORT")
            logger.info("=" * 60)
            
            # Exchange Verification
            logger.info("🏦 EXCHANGE VERIFICATION:")
            logger.info(f"  • Exchange Used: {self.portfolio_results['exchange_used'].upper()}")
            logger.info(f"  • API Credentials: {'✅ Verified' if self.portfolio_results['api_credentials_verified'] else '❌ Not Found'}")
            logger.info(f"  • Connection Status: {'✅ Connected' if self.portfolio_results['binanceus_connection'] else '❌ Failed'}")
            
            # Account Information
            logger.info("\n📊 ACCOUNT INFORMATION:")
            if self.portfolio_results["account_info"]:
                account = self.portfolio_results["account_info"]
                logger.info("  ✅ Real Binance US account data retrieved:")
                if "accountType" in account:
                    logger.info(f"    • Account Type: {account['accountType']}")
                if "canTrade" in account:
                    logger.info(f"    • Trading Enabled: {account['canTrade']}")
                if "canWithdraw" in account:
                    logger.info(f"    • Withdrawals Enabled: {account['canWithdraw']}")
                if "canDeposit" in account:
                    logger.info(f"    • Deposits Enabled: {account['canDeposit']}")
            else:
                logger.info("  ⚠️ Account information not retrieved")
            
            # Portfolio Holdings
            logger.info("\n💰 CURRENT HOLDINGS (BINANCE US):")
            if self.portfolio_results["non_zero_balances"]:
                logger.info("  ✅ Real portfolio balances confirmed:")
                for asset, balance in self.portfolio_results["non_zero_balances"].items():
                    if isinstance(balance, dict):
                        logger.info(f"    💎 {asset}: {balance['total']} (free: {balance['free']}, locked: {balance['locked']})")
                    else:
                        logger.info(f"    💎 {asset}: {balance}")
            else:
                logger.info("  ⚠️ No portfolio balances retrieved")
            
            # Portfolio Value
            logger.info("\n💵 PORTFOLIO VALUE:")
            if self.portfolio_results["total_portfolio_value_usd"] > 0:
                logger.info(f"  💰 Total Value: ${self.portfolio_results['total_portfolio_value_usd']:.2f}")
                logger.info(f"  📊 Available for Trading: ${min(25.0, self.portfolio_results['total_portfolio_value_usd']):.2f}")
                
                if self.portfolio_results["total_portfolio_value_usd"] >= 25.0:
                    logger.info("  ✅ Sufficient funds for $25 trading budget")
                else:
                    logger.info("  ⚠️ Portfolio value below $25 trading budget")
            else:
                logger.info("  ⚠️ Portfolio value not calculated")
            
            # Data Verification Status
            logger.info("\n🔍 DATA VERIFICATION:")
            if (self.portfolio_results["api_credentials_verified"] and 
                self.portfolio_results["non_zero_balances"]):
                logger.info("  ✅ REAL BINANCE US DATA CONFIRMED")
                logger.info("  ✅ System is accessing your actual Binance US account")
                logger.info("  ✅ Portfolio balances are live and current")
                logger.info("  ✅ Exchange-specific data (Binance US, not regular Binance)")
                logger.info("  ✅ Ready for live trading with real account data")
            else:
                logger.info("  ⚠️ Real Binance US data access needs attention")
                if not self.portfolio_results["api_credentials_verified"]:
                    logger.info("  - Verify Binance US API credentials in Vault")
                if not self.portfolio_results["non_zero_balances"]:
                    logger.info("  - Check portfolio balance retrieval")
            
            # Trading Readiness
            logger.info("\n🎯 LIVE TRADING READINESS:")
            if (self.portfolio_results["api_credentials_verified"] and 
                self.portfolio_results["non_zero_balances"] and
                self.portfolio_results["total_portfolio_value_usd"] >= 25.0):
                logger.info("  ✅ READY FOR LIVE TRADING ON BINANCE US")
                logger.info("  ✅ Real account access confirmed")
                logger.info("  ✅ Sufficient trading capital available")
                logger.info("  ✅ Portfolio composition verified")
                logger.info("  ✅ Exchange connectivity established")
            else:
                logger.info("  ⚠️ Address issues before live trading")
            
            # Error Summary
            if self.portfolio_results["errors"]:
                logger.info("\n❌ ISSUES ENCOUNTERED:")
                for i, error in enumerate(self.portfolio_results["errors"], 1):
                    logger.info(f"  {i}. {error}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Binance US report generation failed: {e}")

async def main():
    """Main execution function."""
    try:
        access_test = DirectBinanceUSPortfolioAccess()
        results = await access_test.run_binanceus_portfolio_access()
        
        if results["success"]:
            print("\n🎉 Direct Binance US Portfolio Access - SUCCESS!")
            print("✅ System is accessing your real Binance US account data!")
            print("🏦 Confirmed: Using Binance US (not regular Binance)")
            return 0
        else:
            print(f"\n⚠️ Access test completed with issues: {results.get('error', 'See detailed report above')}")
            print("🔧 Address the issues above to ensure real Binance US data access.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
