#!/usr/bin/env python3
"""
VolexSwarm Autonomous AI Trading System Demonstration
Showcases the complete system with natural language interface and agent coordination.
"""

import requests
import json
import time
from datetime import datetime


class AutonomousSystemDemo:
    """Demonstration of the complete autonomous AI trading system."""
    
    def __init__(self, meta_agent_url="http://localhost:8004"):
        self.meta_agent_url = meta_agent_url
    
    def print_header(self, title):
        """Print a formatted header."""
        print(f"\n{'='*60}")
        print(f"🧠 {title}")
        print(f"{'='*60}")
    
    def print_section(self, title):
        """Print a formatted section."""
        print(f"\n📋 {title}")
        print("-" * 40)
    
    def send_command(self, command):
        """Send a natural language command to the Meta-Agent."""
        try:
            response = requests.post(
                f"{self.meta_agent_url}/command",
                json={"command": command},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def demo_system_status(self):
        """Demonstrate system status and health."""
        self.print_section("System Status & Health Check")
        
        # Get system status
        status_result = self.send_command("status")
        if "error" not in status_result:
            status = status_result["response"]
            print(f"✅ Overall System Status: {status['status']}")
            print(f"🕒 Timestamp: {status['timestamp']}")
            print(f"🤖 Autonomous Mode: {status['autonomous_mode']}")
            
            # Agent status
            print("\n🤝 Agent Status:")
            for agent, agent_status in status["agents"].items():
                status_icon = "✅" if agent_status["status"] == "healthy" else "❌"
                print(f"  {status_icon} {agent}: {agent_status['status']}")
            
            # Infrastructure status
            print(f"\n🗄️  Database: {'✅' if status['database']['status'] == 'healthy' else '❌'}")
            print(f"🔐 Vault: {'✅' if status['vault']['status'] == 'healthy' else '❌'}")
        else:
            print(f"❌ Error: {status_result['error']}")
    
    def demo_natural_language_interface(self):
        """Demonstrate natural language command processing."""
        self.print_section("Natural Language Interface")
        
        # Help command
        print("💬 Testing help command:")
        help_result = self.send_command("help")
        if "error" not in help_result:
            response = help_result["response"]
            print(f"  📝 {response['message']}")
            print("  📋 Examples:")
            for example in response["examples"]:
                print(f"    • {example}")
        else:
            print(f"  ❌ Error: {help_result['error']}")
    
    def demo_market_analysis(self):
        """Demonstrate autonomous market analysis."""
        self.print_section("Autonomous Market Analysis")
        
        symbols = ["BTCUSD", "ETHUSD"]
        
        for symbol in symbols:
            print(f"\n📊 Analyzing {symbol}:")
            analysis_result = self.send_command(f"analyze {symbol}")
            
            if "error" not in analysis_result:
                analysis = analysis_result["response"]["analysis"]
                
                # Market data
                market_data = analysis["market_data"]["data"]
                print(f"  💰 Price: ${market_data['last_price']:,.2f}")
                print(f"  📈 24h Change: {market_data['change_percent_24h']:+.2f}%")
                print(f"  📊 Volume: {market_data['volume_24h']:.2f}")
                
                # Signal
                if "signal" in analysis and "signal" in analysis["signal"]:
                    signal = analysis["signal"]["signal"]
                    signal_icon = "🟢" if signal["signal_type"] == "buy" else "🔴" if signal["signal_type"] == "sell" else "🟡"
                    print(f"  {signal_icon} Signal: {signal['signal_type'].upper()} ({signal['confidence']:.1%} confidence)")
                else:
                    print(f"  🟡 Signal: Not available")
                
                # Insights
                if "insights" in analysis and "insights" in analysis["insights"]:
                    insights = analysis["insights"]["insights"]
                    trend = insights.get('trend', 'Unknown')
                    recommendation = insights.get('recommendation', 'Not available')
                    print(f"  📈 Trend: {trend.title()}")
                    print(f"  💡 Recommendation: {recommendation}")
                else:
                    print(f"  📈 Trend: Not available")
                    print(f"  💡 Recommendation: Not available")
                
                # Technical indicators
                if "indicators" in analysis and "indicators" in analysis["indicators"]:
                    indicators = analysis["indicators"]["indicators"]
                    print(f"  📊 RSI: {indicators['rsi']:.1f}")
                    print(f"  📊 MACD: {indicators['macd']['histogram']:.1f}")
                    print(f"  📊 BB Position: {indicators['bollinger_bands']['position']:.2f}")
                else:
                    print(f"  📊 Technical indicators: Not available")
            else:
                print(f"  ❌ Error: {analysis_result['error']}")
    
    def demo_autonomous_trading(self):
        """Demonstrate autonomous trading decisions."""
        self.print_section("Autonomous Trading Decisions")
        
        symbols = ["BTCUSD", "ETHUSD"]
        
        for symbol in symbols:
            print(f"\n🤖 Autonomous Trade Decision for {symbol}:")
            trade_result = self.send_command(f"trade {symbol} if confident")
            
            if "error" not in trade_result:
                response = trade_result["response"]
                
                if "decision" in response:
                    decision = response["decision"]
                    
                    action_icon = "🟢" if decision["action"] == "buy" else "🔴" if decision["action"] == "sell" else "🟡"
                    print(f"  {action_icon} Decision: {decision['action'].upper()}")
                    print(f"  📊 Confidence: {decision['confidence']:.1%}")
                    print(f"  💰 Position Size: ${decision['position_size']:,.2f}")
                    print(f"  ⚠️  Risk Level: {decision['risk_level']}")
                    print(f"  💭 Reason: {decision['reason']}")
                    
                    if response["action"] == "hold":
                        print(f"  ⏸️  Action: HOLD - {response['reason']}")
                    else:
                        print(f"  ✅ Action: {response['action'].upper()}")
                else:
                    print(f"  🟡 Decision: Not available")
                    print(f"  📊 Action: {response.get('action', 'Unknown')}")
                    print(f"  💭 Reason: {response.get('reason', 'Not available')}")
            else:
                print(f"  ❌ Error: {trade_result['error']}")
    
    def demo_monitoring(self):
        """Demonstrate autonomous monitoring."""
        self.print_section("Autonomous Monitoring")
        
        # Start monitoring
        symbols = ["BTCUSD", "ETHUSD"]
        
        for symbol in symbols:
            print(f"\n👁️  Starting autonomous monitoring for {symbol}:")
            monitor_result = self.send_command(f"monitor {symbol}")
            
            if "error" not in monitor_result:
                response = monitor_result["response"]
                print(f"  ✅ {response['message']}")
                print(f"  🆔 Monitor ID: {response['monitor_id']}")
                print(f"  🕒 Started: {response['timestamp']}")
            else:
                print(f"  ❌ Error: {monitor_result['error']}")
        
        # Get active monitors
        print(f"\n📋 Active Monitors:")
        try:
            response = requests.get(f"{self.meta_agent_url}/monitors", timeout=10)
            if response.status_code == 200:
                monitors_data = response.json()
                print(f"  📊 Total Active Monitors: {monitors_data['count']}")
                for monitor_id, monitor_info in monitors_data["monitors"].items():
                    status_icon = "✅" if monitor_info["active"] else "⏸️"
                    print(f"  {status_icon} {monitor_id}: {monitor_info['symbol']}")
            else:
                print(f"  ❌ Error: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def demo_agent_coordination(self):
        """Demonstrate agent coordination."""
        self.print_section("Agent Coordination")
        
        print("🤝 Testing agent coordination and communication:")
        
        # Test individual agent health
        agents = ["research", "execution", "signal"]
        for agent in agents:
            try:
                response = requests.get(f"{self.meta_agent_url}/agents/{agent}/health", timeout=10)
                if response.status_code == 200:
                    agent_status = response.json()
                    status_icon = "✅" if agent_status["status"] == "healthy" else "❌"
                    print(f"  {status_icon} {agent} agent: {agent_status['status']}")
                else:
                    print(f"  ❌ {agent} agent: HTTP {response.status_code}")
            except Exception as e:
                print(f"  ❌ {agent} agent: {e}")
    
    def run_complete_demo(self):
        """Run the complete autonomous system demonstration."""
        self.print_header("VolexSwarm Autonomous AI Trading System")
        print("🚀 Complete autonomous AI trading system with natural language interface")
        print("🤖 Coordinated by Meta-Agent with autonomous decision making")
        print("📊 Real-time market analysis and trading signals")
        print("👁️  Continuous monitoring and risk management")
        
        # Run all demonstrations
        self.demo_system_status()
        self.demo_natural_language_interface()
        self.demo_market_analysis()
        self.demo_autonomous_trading()
        self.demo_monitoring()
        self.demo_agent_coordination()
        
        # Final summary
        self.print_header("System Summary")
        print("🎉 VolexSwarm Autonomous AI Trading System is fully operational!")
        print("\n✨ Key Features:")
        print("  🤖 Autonomous AI agents with machine learning")
        print("  💬 Natural language interface for human interaction")
        print("  🤝 Intelligent agent coordination and communication")
        print("  📊 Real-time market analysis and signal generation")
        print("  🎯 Autonomous trading decisions with risk management")
        print("  👁️  Continuous monitoring and workflow management")
        print("  🔐 Secure secret management with HashiCorp Vault")
        print("  📈 Time-series data storage with TimescaleDB")
        
        print("\n🚀 Ready for autonomous trading operations!")
        print("💡 Use natural language commands to interact with the system:")
        print("  • 'analyze BTCUSD' - Get comprehensive market analysis")
        print("  • 'trade BTCUSD if confident' - Execute autonomous trade")
        print("  • 'monitor ETHUSD' - Start continuous monitoring")
        print("  • 'status' - Check system health and status")


def main():
    """Main demonstration function."""
    print("Starting VolexSwarm Autonomous AI Trading System Demonstration...")
    
    demo = AutonomousSystemDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main() 