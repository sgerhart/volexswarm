"""
VolexSwarm Enhanced Hybrid Meta Agent - Main Entry Point
Enhanced Meta Agent that serves as the central orchestrator
for all VolexSwarm agents with critical features restored:

✅ RESTORED CRITICAL FEATURES:
- Advanced consensus building with agent voting
- LLM-driven autonomous decision making
- Real-time agent performance monitoring
- Intelligent conflict resolution
- Enhanced task management with priorities
- System intelligence reporting

✅ MAINTAINED FEATURES:
- AutoGen integration for multi-agent coordination
- MCP tool registry for agent coordination
- WebSocket communication hub
- FastAPI REST endpoints

Result: Clean structure with all essential advanced capabilities.
"""

import sys
import os
import asyncio
import signal
from datetime import datetime

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from agents.meta.hybrid_meta_agent import HybridMetaAgent
from common.logging import get_logger

logger = get_logger("enhanced_hybrid_meta_main")

class EnhancedHybridMetaService:
    """Enhanced service wrapper for the hybrid meta agent with critical features restored."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the enhanced hybrid meta agent service."""
        try:
            logger.info("🚀 Starting Enhanced Hybrid Meta Agent Service...")
            logger.info("🔧 Critical features restored: consensus, autonomous decisions, performance monitoring")
            
            # Initialize the enhanced hybrid meta agent
            self.agent = HybridMetaAgent()
            
            # Initialize infrastructure
            await self.agent.initialize()
            
            self.running = True
            
            logger.info("✅ Enhanced Hybrid Meta Agent Service started successfully")
            logger.info("🌐 FastAPI server: http://localhost:8004")
            logger.info("🔌 WebSocket server: ws://localhost:8012 (Central Hub)")
            logger.info("🤝 Consensus building: /consensus/* endpoints")
            logger.info("🧠 Autonomous decisions: /autonomous/* endpoints")
            logger.info("📊 Performance monitoring: /performance/* endpoints")
            logger.info("⚖️ Conflict resolution: /conflicts/* endpoints")
            logger.info("🧩 System intelligence: /intelligence/* endpoints")
            
            # Keep the service running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error starting Enhanced Hybrid Meta Agent Service: {e}")
            raise
            
    async def stop(self):
        """Stop the enhanced hybrid meta agent service."""
        try:
            logger.info("🛑 Stopping Enhanced Hybrid Meta Agent Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
                
            logger.info("✅ Enhanced Hybrid Meta Agent Service stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping Enhanced Hybrid Meta Agent Service: {e}")
            raise

async def main():
    """Main entry point for the enhanced hybrid meta agent service."""
    service = EnhancedHybridMetaService()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        raise
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main()) 