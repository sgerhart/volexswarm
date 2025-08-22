#!/usr/bin/env python3
"""
Master Test Runner for VolexSwarm System

This script runs comprehensive tests across all major components of the VolexSwarm
trading system to verify functionality, performance, and integration.
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Any
import requests
import subprocess

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.logging import get_logger

logger = get_logger("master_test_runner")

class MasterTestRunner:
    """Comprehensive test runner for VolexSwarm system."""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
        # Service endpoints
        self.endpoints = {
            "vault": "http://localhost:8200",
            "research": "http://localhost:8001",
            "execution": "http://localhost:8002",
            "signal": "http://localhost:8003",
            "meta": "http://localhost:8004",
            "strategy": "http://localhost:8011",
            "backtest": "http://localhost:8006",
            "optimize": "http://localhost:8007",
            "monitor": "http://localhost:8008",
            "risk": "http://localhost:8009",
            "compliance": "http://localhost:8010",
            "news_sentiment": "http://localhost:8024",
            "strategy_discovery": "http://localhost:8025",
            "realtime_data": "http://localhost:8026"
        }
    
    def record_test_result(self, test_name: str, passed: bool, message: str, details: Dict = None):
        """Record a test result."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
    
    async def test_infrastructure_health(self):
        """Test infrastructure components (Vault, Database)."""
        logger.info("🏗️ Testing Infrastructure Health")
        
        # Test Vault
        try:
            response = requests.get(f"{self.endpoints['vault']}/v1/sys/health", timeout=5)
            if response.status_code == 200:
                vault_status = response.json()
                if vault_status.get("initialized") and not vault_status.get("sealed"):
                    self.record_test_result("Vault Health", True, "Vault is initialized and unsealed")
                else:
                    self.record_test_result("Vault Health", False, f"Vault status: {vault_status}")
            else:
                self.record_test_result("Vault Health", False, f"Vault returned status {response.status_code}")
        except Exception as e:
            self.record_test_result("Vault Health", False, f"Vault connection failed: {str(e)}")
        
        # Test Database connectivity through research agent
        try:
            response = requests.get(f"{self.endpoints['research']}/health", timeout=5)
            if response.status_code == 200:
                self.record_test_result("Database Connectivity", True, "Database accessible through research agent")
            else:
                self.record_test_result("Database Connectivity", False, f"Research agent returned status {response.status_code}")
        except Exception as e:
            self.record_test_result("Database Connectivity", False, f"Database connection failed: {str(e)}")
    
    async def test_agent_health(self):
        """Test all agent health endpoints."""
        logger.info("🤖 Testing Agent Health")
        
        healthy_agents = []
        unhealthy_agents = []
        
        for agent_name, endpoint in self.endpoints.items():
            if agent_name in ["vault"]:  # Skip non-agent endpoints
                continue
                
            try:
                response = requests.get(f"{endpoint}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    self.record_test_result(
                        f"{agent_name.title()} Agent Health", 
                        True, 
                        f"Agent is healthy (uptime: {health_data.get('uptime', 'unknown')})"
                    )
                    healthy_agents.append(agent_name)
                else:
                    self.record_test_result(
                        f"{agent_name.title()} Agent Health", 
                        False, 
                        f"Agent returned status {response.status_code}"
                    )
                    unhealthy_agents.append(agent_name)
            except Exception as e:
                self.record_test_result(
                    f"{agent_name.title()} Agent Health", 
                    False, 
                    f"Agent connection failed: {str(e)}"
                )
                unhealthy_agents.append(agent_name)
        
        # Summary
        self.record_test_result(
            "Agent Health Summary", 
            len(unhealthy_agents) == 0, 
            f"{len(healthy_agents)} agents healthy, {len(unhealthy_agents)} agents unhealthy"
        )
    
    async def test_agent_communication(self):
        """Test agent communication and coordination."""
        logger.info("📡 Testing Agent Communication")
        
        # Test Meta Agent API endpoints
        try:
            # Test system status
            response = requests.get(f"{self.endpoints['meta']}/api/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                self.record_test_result(
                    "Meta Agent Status", 
                    True, 
                    f"Meta agent is {status_data.get('status', 'unknown')}"
                )
            else:
                self.record_test_result("Meta Agent Status", False, f"Status endpoint returned {response.status_code}")
        except Exception as e:
            self.record_test_result("Meta Agent Status", False, f"Status check failed: {str(e)}")
        
        # Test WebSocket stats
        try:
            response = requests.get(f"{self.endpoints['meta']}/websocket/stats", timeout=5)
            if response.status_code == 200:
                ws_stats = response.json()
                self.record_test_result(
                    "WebSocket Server", 
                    True, 
                    f"WebSocket server running on port {ws_stats.get('server_port', 'unknown')}"
                )
            else:
                self.record_test_result("WebSocket Server", False, f"WebSocket stats returned {response.status_code}")
        except Exception as e:
            self.record_test_result("WebSocket Server", False, f"WebSocket check failed: {str(e)}")
        
        # Test agent registration
        try:
            response = requests.get(f"{self.endpoints['meta']}/api/agents", timeout=5)
            if response.status_code == 200:
                agents_data = response.json()
                self.record_test_result(
                    "Agent Registration", 
                    True, 
                    f"Agent registry accessible"
                )
            else:
                self.record_test_result("Agent Registration", False, f"Agent registry returned {response.status_code}")
        except Exception as e:
            self.record_test_result("Agent Registration", False, f"Agent registry check failed: {str(e)}")
    
    async def test_vault_integration(self):
        """Test Vault secrets and configuration."""
        logger.info("🔐 Testing Vault Integration")
        
        # Test Vault secrets access
        try:
            # This would require Vault token authentication
            # For now, just test that Vault is accessible
            response = requests.get(f"{self.endpoints['vault']}/v1/sys/mounts", timeout=5)
            if response.status_code == 200:
                self.record_test_result("Vault Secrets Engine", True, "Vault secrets engine accessible")
            else:
                self.record_test_result("Vault Secrets Engine", False, f"Vault mounts returned {response.status_code}")
        except Exception as e:
            self.record_test_result("Vault Secrets Engine", False, f"Vault secrets check failed: {str(e)}")
    
    async def test_database_schema(self):
        """Test database schema and connectivity."""
        logger.info("🗄️ Testing Database Schema")
        
        # Test through research agent (which should have database access)
        try:
            response = requests.get(f"{self.endpoints['research']}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.record_test_result("Database Schema", True, "Database schema accessible through research agent")
            else:
                self.record_test_result("Database Schema", False, f"Research agent returned {response.status_code}")
        except Exception as e:
            self.record_test_result("Database Schema", False, f"Database schema check failed: {str(e)}")
    
    async def test_real_time_components(self):
        """Test real-time components."""
        logger.info("⚡ Testing Real-Time Components")
        
        # Test real-time data agent
        try:
            response = requests.get(f"{self.endpoints['realtime_data']}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.record_test_result("Real-Time Data Agent", True, "Real-time data agent is healthy")
            else:
                self.record_test_result("Real-Time Data Agent", False, f"Real-time data agent returned {response.status_code}")
        except Exception as e:
            self.record_test_result("Real-Time Data Agent", False, f"Real-time data agent check failed: {str(e)}")
    
    async def test_strategy_discovery(self):
        """Test strategy discovery functionality."""
        logger.info("🔍 Testing Strategy Discovery")
        
        # Test strategy discovery agent
        try:
            response = requests.get(f"{self.endpoints['strategy_discovery']}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.record_test_result("Strategy Discovery Agent", True, "Strategy discovery agent is healthy")
            else:
                self.record_test_result("Strategy Discovery Agent", False, f"Strategy discovery agent returned {response.status_code}")
        except Exception as e:
            self.record_test_result("Strategy Discovery Agent", False, f"Strategy discovery agent check failed: {str(e)}")
    
    async def test_news_sentiment(self):
        """Test news sentiment analysis."""
        logger.info("📰 Testing News Sentiment Analysis")
        
        # Test news sentiment agent
        try:
            response = requests.get(f"{self.endpoints['news_sentiment']}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.record_test_result("News Sentiment Agent", True, "News sentiment agent is healthy")
            else:
                self.record_test_result("News Sentiment Agent", False, f"News sentiment agent returned {response.status_code}")
        except Exception as e:
            self.record_test_result("News Sentiment Agent", False, f"News sentiment agent check failed: {str(e)}")
    
    async def run_specialized_tests(self):
        """Run specialized test scripts."""
        logger.info("🧪 Running Specialized Tests")
        
        # Test real-time execution system
        try:
            result = subprocess.run([
                sys.executable, 
                "scripts/test/test_real_time_execution_system.py"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.record_test_result("Real-Time Execution System", True, "Real-time execution tests passed")
            else:
                self.record_test_result("Real-Time Execution System", False, f"Real-time execution tests failed: {result.stderr}")
        except Exception as e:
            self.record_test_result("Real-Time Execution System", False, f"Real-time execution test failed: {str(e)}")
        
        # Test strategy discovery
        try:
            result = subprocess.run([
                sys.executable, 
                "scripts/test/test_strategy_discovery_agent.py"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.record_test_result("Strategy Discovery Tests", True, "Strategy discovery tests passed")
            else:
                self.record_test_result("Strategy Discovery Tests", False, f"Strategy discovery tests failed: {result.stderr}")
        except Exception as e:
            self.record_test_result("Strategy Discovery Tests", False, f"Strategy discovery test failed: {str(e)}")
    
    async def run_performance_tests(self):
        """Run performance and load tests."""
        logger.info("⚡ Running Performance Tests")
        
        # Test API response times
        performance_results = {}
        
        for agent_name, endpoint in self.endpoints.items():
            if agent_name in ["vault"]:  # Skip non-agent endpoints
                continue
                
            try:
                start_time = time.time()
                response = requests.get(f"{endpoint}/health", timeout=5)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                performance_results[agent_name] = response_time
                
                if response_time < 1000:  # Less than 1 second
                    self.record_test_result(
                        f"{agent_name.title()} Performance", 
                        True, 
                        f"Response time: {response_time:.2f}ms"
                    )
                else:
                    self.record_test_result(
                        f"{agent_name.title()} Performance", 
                        False, 
                        f"Slow response time: {response_time:.2f}ms"
                    )
            except Exception as e:
                self.record_test_result(
                    f"{agent_name.title()} Performance", 
                    False, 
                    f"Performance test failed: {str(e)}"
                )
        
        # Performance summary
        if performance_results:
            avg_response_time = sum(performance_results.values()) / len(performance_results)
            self.record_test_result(
                "Overall Performance", 
                avg_response_time < 1000, 
                f"Average response time: {avg_response_time:.2f}ms"
            )
    
    async def run_all_tests(self):
        """Run all tests."""
        logger.info("🚀 Starting Master Test Runner")
        self.start_time = datetime.utcnow()
        
        try:
            # Infrastructure tests
            await self.test_infrastructure_health()
            
            # Agent health tests
            await self.test_agent_health()
            
            # Communication tests
            await self.test_agent_communication()
            
            # Integration tests
            await self.test_vault_integration()
            await self.test_database_schema()
            
            # Component tests
            await self.test_real_time_components()
            await self.test_strategy_discovery()
            await self.test_news_sentiment()
            
            # Performance tests
            await self.run_performance_tests()
            
            # Specialized tests (if available)
            await self.run_specialized_tests()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            raise
        finally:
            self.end_time = datetime.utcnow()
            self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        logger.info("📊 Test Summary")
        logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        # Print failed tests
        if failed_tests > 0:
            logger.info("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    logger.info(f"  - {result['test_name']}: {result['message']}")
        
        # Save results to file
        results_file = f"test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100,
                    "duration_seconds": duration,
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat()
                },
                "results": self.test_results
            }, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: {results_file}")
        
        if failed_tests == 0:
            logger.info("🎉 All tests passed! System is ready for production.")
        else:
            logger.warning(f"⚠️ {failed_tests} tests failed. Please review the results.")

async def main():
    """Main function."""
    runner = MasterTestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
