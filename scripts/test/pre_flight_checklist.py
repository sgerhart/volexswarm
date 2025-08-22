#!/usr/bin/env python3
"""
VolexSwarm Pre-Flight Checklist for Real-World Trading
Verifies all systems are ready for live trading with Binance US.

This script checks:
- Vault connectivity and credentials
- Database connectivity
- Agent initialization
- Exchange connectivity
- Risk management settings
- Safety limits
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.logging import get_logger
from common.vault import get_vault_client, get_exchange_credentials, health_check as vault_health_check
from common.db import get_db_client, health_check as db_health_check
from agents.execution.agentic_execution_agent import AgenticExecutionAgent

logger = get_logger("pre_flight_checklist")

class PreFlightChecker:
    """Pre-flight checklist for real-world trading."""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
        self.all_passed = True
    
    def add_check(self, name: str, status: bool, message: str, critical: bool = True):
        """Add a check result."""
        check = {
            "name": name,
            "status": status,
            "message": message,
            "critical": critical,
            "timestamp": datetime.now()
        }
        self.checks.append(check)
        
        if not status:
            if critical:
                self.errors.append(check)
                self.all_passed = False
            else:
                self.warnings.append(check)
        
        # Log the result
        if status:
            logger.info(f"✅ {name}: {message}")
        elif critical:
            logger.error(f"❌ {name}: {message}")
        else:
            logger.warning(f"⚠️ {name}: {message}")
    
    async def check_vault_connectivity(self):
        """Check Vault connectivity and health."""
        try:
            vault_healthy = vault_health_check()
            if vault_healthy:
                self.add_check(
                    "Vault Connectivity",
                    True,
                    "Vault is accessible and authenticated"
                )
            else:
                self.add_check(
                    "Vault Connectivity",
                    False,
                    "Vault is not accessible or authentication failed"
                )
        except Exception as e:
            self.add_check(
                "Vault Connectivity",
                False,
                f"Vault connection error: {e}"
            )
    
    async def check_exchange_credentials(self):
        """Check Binance US credentials in Vault."""
        try:
            credentials = get_exchange_credentials("binance")
            if credentials and "api_key" in credentials and "secret" in credentials:
                # Mask the credentials for logging
                masked_key = credentials["api_key"][:8] + "..." if len(credentials["api_key"]) > 8 else "***"
                self.add_check(
                    "Binance Credentials",
                    True,
                    f"Binance US credentials found (API Key: {masked_key})"
                )
            else:
                self.add_check(
                    "Binance Credentials",
                    False,
                    "Binance US credentials not found in Vault"
                )
        except Exception as e:
            self.add_check(
                "Binance Credentials",
                False,
                f"Error retrieving Binance credentials: {e}"
            )
    
    async def check_database_connectivity(self):
        """Check database connectivity."""
        try:
            db_healthy = await db_health_check()
            if db_healthy:
                self.add_check(
                    "Database Connectivity",
                    True,
                    "Database is accessible and responsive"
                )
            else:
                self.add_check(
                    "Database Connectivity",
                    False,
                    "Database is not accessible"
                )
        except Exception as e:
            self.add_check(
                "Database Connectivity",
                False,
                f"Database connection error: {e}"
            )
    
    async def check_exchange_connectivity(self):
        """Check Binance US exchange connectivity."""
        try:
            # Initialize execution agent to test exchange connection
            execution_agent = AgenticExecutionAgent()
            await execution_agent.initialize()
            
            # Test portfolio status call
            portfolio_status = await execution_agent.get_portfolio_status("binance")
            
            if portfolio_status.get("status") == "success":
                balance = portfolio_status.get("balance", {}).get("USDT", 0.0)
                self.add_check(
                    "Exchange Connectivity",
                    True,
                    f"Binance US connection successful (USDT Balance: {balance:.2f})"
                )
                
                # Check minimum balance for trading
                if balance >= 25.0:
                    self.add_check(
                        "Trading Balance",
                        True,
                        f"Sufficient balance for testing ({balance:.2f} USDT >= 25.00 USDT)"
                    )
                else:
                    self.add_check(
                        "Trading Balance",
                        False,
                        f"Insufficient balance for testing ({balance:.2f} USDT < 25.00 USDT)"
                    )
            else:
                self.add_check(
                    "Exchange Connectivity",
                    False,
                    f"Binance US connection failed: {portfolio_status.get('message', 'Unknown error')}"
                )
            
            await execution_agent.shutdown()
            
        except Exception as e:
            self.add_check(
                "Exchange Connectivity",
                False,
                f"Exchange connection test failed: {e}"
            )
    
    async def check_agent_dependencies(self):
        """Check agent dependencies and imports."""
        try:
            # Test agent imports
            from agents.realtime_data.agentic_realtime_data_agent import AgenticRealtimeDataAgent
            from agents.news_sentiment.agentic_news_sentiment_agent import AgenticNewsSentimentAgent
            from agents.strategy_discovery.agentic_strategy_discovery_agent import AgenticStrategyDiscoveryAgent
            from agents.monitor.agentic_monitor_agent import AgenticMonitorAgent
            
            self.add_check(
                "Agent Dependencies",
                True,
                "All agent modules imported successfully"
            )
        except Exception as e:
            self.add_check(
                "Agent Dependencies",
                False,
                f"Agent import error: {e}"
            )
    
    async def check_risk_management_settings(self):
        """Check risk management configuration."""
        try:
            # Check if risk management tables exist in database
            db_client = get_db_client()
            if db_client:
                # Check for risk_management table
                result = await db_client.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'risk_management'
                """)
                
                if result:
                    self.add_check(
                        "Risk Management Tables",
                        True,
                        "Risk management database tables exist"
                    )
                else:
                    self.add_check(
                        "Risk Management Tables",
                        False,
                        "Risk management database tables not found",
                        critical=False
                    )
            else:
                self.add_check(
                    "Risk Management Tables",
                    False,
                    "Cannot check risk management tables - no database connection",
                    critical=False
                )
        except Exception as e:
            self.add_check(
                "Risk Management Tables",
                False,
                f"Error checking risk management tables: {e}",
                critical=False
            )
    
    async def check_openai_credentials(self):
        """Check OpenAI API credentials."""
        try:
            vault_client = get_vault_client()
            openai_secret = vault_client.get_secret("openai/api_key")
            
            if openai_secret and "api_key" in openai_secret:
                masked_key = openai_secret["api_key"][:8] + "..." if len(openai_secret["api_key"]) > 8 else "***"
                self.add_check(
                    "OpenAI Credentials",
                    True,
                    f"OpenAI API key found (Key: {masked_key})"
                )
            else:
                self.add_check(
                    "OpenAI Credentials",
                    False,
                    "OpenAI API key not found in Vault",
                    critical=False
                )
        except Exception as e:
            self.add_check(
                "OpenAI Credentials",
                False,
                f"Error checking OpenAI credentials: {e}",
                critical=False
            )
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all pre-flight checks."""
        logger.info("🚀 Starting VolexSwarm Pre-Flight Checklist")
        logger.info("=" * 60)
        
        # Run all checks
        await self.check_vault_connectivity()
        await self.check_exchange_credentials()
        await self.check_database_connectivity()
        await self.check_exchange_connectivity()
        await self.check_agent_dependencies()
        await self.check_risk_management_settings()
        await self.check_openai_credentials()
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("📊 PRE-FLIGHT CHECKLIST SUMMARY")
        logger.info(f"Total Checks: {len(self.checks)}")
        logger.info(f"Passed: {len([c for c in self.checks if c['status']])}")
        logger.info(f"Failed: {len(self.errors)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        
        if self.all_passed:
            logger.info("✅ ALL CRITICAL CHECKS PASSED - SYSTEM READY FOR LIVE TRADING")
        else:
            logger.error("❌ CRITICAL CHECKS FAILED - DO NOT PROCEED WITH LIVE TRADING")
            logger.error("Failed checks:")
            for error in self.errors:
                logger.error(f"  - {error['name']}: {error['message']}")
        
        if self.warnings:
            logger.warning("⚠️ Warnings (non-critical):")
            for warning in self.warnings:
                logger.warning(f"  - {warning['name']}: {warning['message']}")
        
        return {
            "all_passed": self.all_passed,
            "total_checks": len(self.checks),
            "passed_checks": len([c for c in self.checks if c['status']]),
            "failed_checks": len(self.errors),
            "warnings": len(self.warnings),
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings
        }

async def main():
    """Main pre-flight check execution."""
    try:
        checker = PreFlightChecker()
        results = await checker.run_all_checks()
        
        # Save results to file
        results_file = "/tmp/volexswarm_preflight_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📄 Results saved to: {results_file}")
        
        return 0 if results["all_passed"] else 1
        
    except Exception as e:
        logger.error(f"❌ Pre-flight check failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
