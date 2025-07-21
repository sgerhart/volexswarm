#!/usr/bin/env python3
"""
Test script for VolexSwarm Meta-Agent.
Tests natural language processing, agent coordination, and autonomous features.
"""

import requests
import json
import time
import sys
from datetime import datetime


class MetaAgentTester:
    """Test suite for Meta-Agent functionality."""
    
    def __init__(self, base_url="http://localhost:8004"):
        self.base_url = base_url
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_health_check(self):
        """Test Meta-Agent health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", True, f"Status: {data.get('status')}")
                    return True
                else:
                    self.log_test("Health Check", False, f"Status: {data.get('status')}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    def test_system_status(self):
        """Test system status endpoint."""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "unhealthy"]:
                    self.log_test("System Status", True, f"Overall: {data.get('status')}")
                    
                    # Check individual agents
                    agents = data.get("agents", {})
                    for agent, status in agents.items():
                        agent_status = status.get("status", "unknown")
                        self.log_test(f"  {agent} Agent", agent_status == "healthy", f"Status: {agent_status}")
                    
                    return True
                else:
                    self.log_test("System Status", False, "Invalid status response")
                    return False
            else:
                self.log_test("System Status", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("System Status", False, str(e))
            return False
    
    def test_natural_language_help(self):
        """Test natural language help command."""
        try:
            response = requests.post(
                f"{self.base_url}/command",
                json={"command": "help"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("response", {}).get("type") == "help":
                    self.log_test("NLP Help Command", True, "Help response received")
                    return True
                else:
                    self.log_test("NLP Help Command", False, "Invalid help response")
                    return False
            else:
                self.log_test("NLP Help Command", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("NLP Help Command", False, str(e))
            return False
    
    def test_natural_language_status(self):
        """Test natural language status command."""
        try:
            response = requests.post(
                f"{self.base_url}/command",
                json={"command": "status"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("response", {}).get("status"):
                    self.log_test("NLP Status Command", True, "Status response received")
                    return True
                else:
                    self.log_test("NLP Status Command", False, "Invalid status response")
                    return False
            else:
                self.log_test("NLP Status Command", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("NLP Status Command", False, str(e))
            return False
    
    def test_natural_language_analyze(self):
        """Test natural language analyze command."""
        try:
            response = requests.post(
                f"{self.base_url}/command",
                json={"command": "analyze BTCUSD"},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("response", {}).get("symbol") == "BTCUSD":
                    self.log_test("NLP Analyze Command", True, "Analysis response received")
                    return True
                else:
                    self.log_test("NLP Analyze Command", False, "Invalid analysis response")
                    return False
            else:
                self.log_test("NLP Analyze Command", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("NLP Analyze Command", False, str(e))
            return False
    
    def test_natural_language_trade(self):
        """Test natural language trade command."""
        try:
            response = requests.post(
                f"{self.base_url}/command",
                json={"command": "trade BTCUSD if confident"},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("response", {}).get("symbol") == "BTCUSD":
                    self.log_test("NLP Trade Command", True, "Trade response received")
                    return True
                else:
                    self.log_test("NLP Trade Command", False, "Invalid trade response")
                    return False
            else:
                self.log_test("NLP Trade Command", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("NLP Trade Command", False, str(e))
            return False
    
    def test_natural_language_monitor(self):
        """Test natural language monitor command."""
        try:
            response = requests.post(
                f"{self.base_url}/command",
                json={"command": "monitor ETHUSD"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("response", {}).get("symbol") == "ETHUSD":
                    self.log_test("NLP Monitor Command", True, "Monitor response received")
                    return True
                else:
                    self.log_test("NLP Monitor Command", False, "Invalid monitor response")
                    return False
            else:
                self.log_test("NLP Monitor Command", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("NLP Monitor Command", False, str(e))
            return False
    
    def test_direct_analyze_endpoint(self):
        """Test direct analyze endpoint."""
        try:
            response = requests.post(f"{self.base_url}/analyze/BTCUSD", timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("symbol") == "BTCUSD":
                    self.log_test("Direct Analyze Endpoint", True, "Analysis completed")
                    return True
                else:
                    self.log_test("Direct Analyze Endpoint", False, "Invalid analysis response")
                    return False
            else:
                self.log_test("Direct Analyze Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Direct Analyze Endpoint", False, str(e))
            return False
    
    def test_direct_trade_endpoint(self):
        """Test direct trade endpoint."""
        try:
            response = requests.post(
                f"{self.base_url}/trade/BTCUSD",
                params={"action": "auto", "confidence": 0.7},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("symbol") == "BTCUSD":
                    self.log_test("Direct Trade Endpoint", True, "Trade decision made")
                    return True
                else:
                    self.log_test("Direct Trade Endpoint", False, "Invalid trade response")
                    return False
            else:
                self.log_test("Direct Trade Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Direct Trade Endpoint", False, str(e))
            return False
    
    def test_monitor_endpoint(self):
        """Test monitor endpoint."""
        try:
            response = requests.post(f"{self.base_url}/monitor/ETHUSD", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("symbol") == "ETHUSD" and data.get("monitor_id"):
                    self.log_test("Monitor Endpoint", True, f"Monitor started: {data.get('monitor_id')}")
                    return True
                else:
                    self.log_test("Monitor Endpoint", False, "Invalid monitor response")
                    return False
            else:
                self.log_test("Monitor Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Monitor Endpoint", False, str(e))
            return False
    
    def test_monitors_list(self):
        """Test monitors list endpoint."""
        try:
            response = requests.get(f"{self.base_url}/monitors", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "monitors" in data:
                    self.log_test("Monitors List", True, f"Found {data.get('count', 0)} monitors")
                    return True
                else:
                    self.log_test("Monitors List", False, "Invalid monitors response")
                    return False
            else:
                self.log_test("Monitors List", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Monitors List", False, str(e))
            return False
    
    def test_agent_health_endpoints(self):
        """Test individual agent health endpoints."""
        agents = ["research", "execution", "signal"]
        
        for agent in agents:
            try:
                response = requests.get(f"{self.base_url}/agents/{agent}/health", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    self.log_test(f"Agent Health - {agent}", status == "healthy", f"Status: {status}")
                else:
                    self.log_test(f"Agent Health - {agent}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Agent Health - {agent}", False, str(e))
    
    def run_all_tests(self):
        """Run all Meta-Agent tests."""
        print("🧠 VolexSwarm Meta-Agent Test Suite")
        print("=" * 50)
        print(f"Testing Meta-Agent at: {self.base_url}")
        print()
        
        # Basic functionality tests
        print("📋 Basic Functionality Tests:")
        print("-" * 30)
        self.test_health_check()
        self.test_system_status()
        
        # Natural language processing tests
        print("\n💬 Natural Language Processing Tests:")
        print("-" * 40)
        self.test_natural_language_help()
        self.test_natural_language_status()
        self.test_natural_language_analyze()
        self.test_natural_language_trade()
        self.test_natural_language_monitor()
        
        # Direct API endpoint tests
        print("\n🔌 Direct API Endpoint Tests:")
        print("-" * 30)
        self.test_direct_analyze_endpoint()
        self.test_direct_trade_endpoint()
        self.test_monitor_endpoint()
        self.test_monitors_list()
        
        # Agent coordination tests
        print("\n🤝 Agent Coordination Tests:")
        print("-" * 30)
        self.test_agent_health_endpoints()
        
        # Summary
        print("\n📊 Test Summary:")
        print("-" * 20)
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! Meta-Agent is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the details above.")
        
        return passed == total


def main():
    """Main test function."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8004"
    
    tester = MetaAgentTester(base_url)
    success = tester.run_all_tests()
    
    # Save test results
    with open("meta_agent_test_results.json", "w") as f:
        json.dump(tester.test_results, f, indent=2)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 