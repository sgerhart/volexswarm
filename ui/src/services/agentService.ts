import axios from 'axios';
import { AgentIntelligence, PortfolioData, TradingSignal, ProductionStrategy } from '../types';

// Only communicate with the Meta Agent - it handles all other agents
const META_AGENT_ENDPOINT = 'http://localhost:8004';

// Axios instance with default config
const api = axios.create({
  timeout: 15000, // Increased timeout for Meta Agent coordination
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check for all agents - Get REAL data from Meta Agent
export const checkAgentHealth = async (): Promise<AgentIntelligence[]> => {
  try {
    // Use the Meta Agent's performance overview endpoint
    const response = await api.get(`${META_AGENT_ENDPOINT}/performance/overview`);
    if (response.status === 200 && response.data.performance_overview) {
      const agents: AgentIntelligence[] = [];
      
      // Transform real Meta Agent data to our interface
      for (const [name, data] of Object.entries(response.data.performance_overview)) {
        const agentData = data as any;
        agents.push({
          agentName: `${name.charAt(0).toUpperCase() + name.slice(1)} Agent`,
          status: agentData.current_status?.status || 'unknown',
          currentTask: agentData.current_status?.agent || 'System monitoring',
          capabilities: getDefaultCapabilities(name),
          performance: {
            tasksCompleted: agentData.recent_tasks || 0,
            successRate: agentData.success_rate || 0,
            avgResponseTime: agentData.average_completion_time || 0,
            lastActive: agentData.timestamp || 'Unknown',
            uptime: agentData.current_status?.uptime || 'Unknown',
          },
          autonomousDecisions: [],
          port: 8004, // Meta Agent port
          endpoint: META_AGENT_ENDPOINT,
        });
      }
      
      return agents;
    }
  } catch (error) {
    console.error('Failed to fetch real agent data from Meta Agent:', error);
  }
  
  // Fallback to basic health check if Meta Agent fails
  try {
    const response = await api.get(`${META_AGENT_ENDPOINT}/health`);
    if (response.status === 200) {
      return [{
        agentName: "Meta Agent",
        status: 'healthy',
        currentTask: 'System monitoring',
        capabilities: getDefaultCapabilities('meta'),
        performance: {
          tasksCompleted: 0,
          successRate: 0,
          avgResponseTime: 0,
          lastActive: 'Just now',
          uptime: 'Unknown',
        },
        autonomousDecisions: [],
        port: 8004,
        endpoint: META_AGENT_ENDPOINT,
      }];
    }
  } catch (error) {
    console.error('Meta Agent health check failed:', error);
  }
  
  return [];
};

// Get default capabilities for each agent type
const getDefaultCapabilities = (agentName: string): string[] => {
  const capabilities: Record<string, string[]> = {
    research: ['Market Research', 'Sentiment Analysis', 'Data Collection'],
    signal: ['Technical Analysis', 'Signal Generation', 'Pattern Recognition'],
    execution: ['Trade Execution', 'Order Management', 'Position Tracking'],
    strategy: ['Strategy Development', 'Optimization', 'Backtesting'],
    risk: ['Risk Assessment', 'Position Sizing', 'Portfolio Protection'],
    compliance: ['Audit Trails', 'Regulatory Checks', 'KYC/AML'],
    backtest: ['Historical Analysis', 'Performance Evaluation', 'Strategy Validation'],
    optimize: ['Parameter Optimization', 'Performance Tuning', 'Strategy Refinement'],
    monitor: ['System Monitoring', 'Performance Tracking', 'Alert Generation'],
    newsSentiment: ['News Analysis', 'Sentiment Scoring', 'Impact Assessment'],
    strategyDiscovery: ['Strategy Discovery', 'Pattern Recognition', 'AI Optimization'],
    realtimeData: ['Live Data Streaming', 'Market Data', 'Real-time Updates'],
    meta: ['Agent Coordination', 'Workflow Management', 'System Orchestration'],
  };
  
  return capabilities[agentName] || ['General Operations'];
};

// Get portfolio data through Meta Agent coordination
export const getPortfolioData = async (): Promise<PortfolioData | null> => {
  try {
    console.log('🔍 Calling Meta Agent portfolio endpoint...');
    
    // Use Meta Agent's portfolio coordination endpoint
    const response = await api.get(`${META_AGENT_ENDPOINT}/coordinate/portfolio`);
    
    if (response.status === 200 && response.data) {
      console.log('✅ Received portfolio data from Meta Agent:', response.data);
      
      // Transform Meta Agent response to our interface
      const metaData = response.data;
      
      // Extract portfolio value from the nested structure
      const portfolioValue = metaData.portfolio?.portfolio_status?.portfolio_value || 0;
      const positions = metaData.portfolio?.portfolio_status?.positions || [];
      
      // Transform positions to match UI expectations
      const transformedPositions = positions.map((pos: any) => ({
        symbol: pos.symbol,
        quantity: pos.amount,
        averagePrice: pos.current_price, // Using current price as fallback
        currentPrice: pos.current_price,
        totalValue: pos.usdt_value,
        unrealizedPnL: 0, // Not provided by current API
        realizedPnL: 0,   // Not provided by current API
        allocation: portfolioValue > 0 ? (pos.usdt_value / portfolioValue) * 100 : 0
      }));
      
      const portfolioData = {
        totalValue: portfolioValue,
        unrealizedPnL: metaData.portfolio?.pnl?.unrealized_pnl || 0,
        realizedPnL: metaData.portfolio?.pnl?.realized_pnl || 0,
        positions: transformedPositions,
        timestamp: new Date().toISOString(),
        performance: {
          totalReturn: metaData.portfolio?.performance?.total_return_percentage || 0,
          sharpeRatio: 0, // Not provided by current API
          maxDrawdown: 0, // Not provided by current API
          winRate: 0,     // Not provided by current API
          profitFactor: 0, // Not provided by current API
          totalTrades: metaData.portfolio?.performance?.positions_count || 0,
          winningTrades: 0, // Not provided by current API
          losingTrades: 0,  // Not provided by current API
          averageWin: 0,    // Not provided by current API
          averageLoss: 0,   // Not provided by current API
        },
        history: metaData.portfolio?.history || null // Added portfolio history
      };
      
      console.log('✅ Transformed portfolio data:', portfolioData);
      return portfolioData;
    }
  } catch (error) {
    console.error('❌ Failed to fetch portfolio data from Meta Agent:', error);
  }
  
  return null;
};

// Get portfolio history data for charting
export const getPortfolioHistory = async (days: number = 30): Promise<any[] | null> => {
  try {
    console.log(`📈 Fetching portfolio history for ${days} days...`);
    
    // Call Execution Agent directly for portfolio history
    const response = await api.get(`http://localhost:8002/api/execution/portfolio-history?days=${days}`);
    
    if (response.status === 200 && response.data?.data_points) {
      console.log('✅ Received portfolio history data:', response.data);
      
      // Transform the data to match the ChartDataPoint interface
      const transformedData = response.data.data_points.map((point: any) => ({
        timestamp: point.timestamp,
        portfolio_value: point.portfolio_value,
        total_return_percentage: point.total_return_percentage,
        usdt_balance: point.usdt_balance,
        btc_balance: point.btc_balance
      }));
      
      return transformedData;
    } else {
      console.log('⚠️ No portfolio history data available');
      return null;
    }
  } catch (error) {
    console.error('❌ Failed to fetch portfolio history:', error);
    return null;
  }
};

// Get trading signals through Meta Agent
export const getTradingSignals = async (): Promise<TradingSignal[]> => {
  try {
    // Use Meta Agent's signal coordination endpoint
    const response = await api.get(`${META_AGENT_ENDPOINT}/coordinate/signals`);
    if (response.status === 200 && response.data) {
      return response.data.signals || [];
    }
  } catch (error) {
    console.error('Failed to fetch trading signals from Meta Agent:', error);
  }
  return [];
};

// Get active strategies through Meta Agent
export const getActiveStrategies = async (): Promise<ProductionStrategy[]> => {
  try {
    // Use Meta Agent's strategy coordination endpoint
    const response = await api.get(`${META_AGENT_ENDPOINT}/coordinate/strategies`);
    if (response.status === 200 && response.data) {
      return response.data.strategies || [];
    }
  } catch (error) {
    console.error('Failed to fetch active strategies from Meta Agent:', error);
  }
  return [];
};

// Get market data through Meta Agent
export const getMarketData = async (): Promise<any[]> => {
  try {
    // Use Meta Agent's market data coordination endpoint
    const response = await api.get(`${META_AGENT_ENDPOINT}/coordinate/market`);
    if (response.status === 200 && response.data) {
      return response.data.market_data || [];
    }
  } catch (error) {
    console.error('Failed to fetch market data from Meta Agent:', error);
  }
  return [];
};

// Execute a task through the meta agent
export const executeTask = async (taskDescription: string, agents: string[]): Promise<any> => {
  try {
    const response = await api.post(`${META_AGENT_ENDPOINT}/autogen/execute`, {
      description: taskDescription,
      agents: agents,
    });
    if (response.status === 200) {
      return response.data;
    }
  } catch (error) {
    console.error('Failed to execute task:', error);
  }
  return null;
};

// Get system intelligence from Meta Agent - REAL DATA
export const getSystemIntelligence = async (): Promise<any> => {
  try {
    const response = await api.get(`${META_AGENT_ENDPOINT}/intelligence/system`);
    if (response.status === 200) {
      return response.data;
    }
  } catch (error) {
    console.error('Failed to fetch system intelligence:', error);
  }
  return null;
};

// Get task status from meta agent
export const getTaskStatus = async (taskId: string): Promise<any> => {
  try {
    const response = await api.get(`${META_AGENT_ENDPOINT}/api/tasks/${taskId}`);
    if (response.status === 200) {
      return response.data;
    }
  } catch (error) {
    console.error('Failed to get task status:', error);
  }
  return null;
};

// WebSocket connection for real-time updates
let wsConnection: WebSocket | null = null;
let wsMessageHandler: ((data: any) => void) | null = null;

export const createWebSocketConnection = (onMessage: (data: any) => void) => {
  // If we already have a connection, don't create another one
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    console.log('WebSocket already connected, reusing existing connection');
    wsMessageHandler = onMessage;
    return wsConnection;
  }
  
  // Close any existing connection
  if (wsConnection) {
    wsConnection.close();
    wsConnection = null;
  }
  
  try {
    // Use correct port 8004 for Meta Agent
    const ws = new WebSocket('ws://localhost:8004/ws');
    wsConnection = ws;
    wsMessageHandler = onMessage;
    
    ws.onopen = () => {
      console.log('🔌 WebSocket connected to Meta Agent');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (wsMessageHandler) {
          wsMessageHandler(data);
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket connection closed');
      wsConnection = null;
      wsMessageHandler = null;
    };
    
    return ws;
  } catch (error) {
    console.error('Failed to create WebSocket connection:', error);
    return null;
  }
};

// Close WebSocket connection
export const closeWebSocketConnection = () => {
  if (wsConnection) {
    wsConnection.close();
    wsConnection = null;
    wsMessageHandler = null;
  }
};

// Update message handler for existing connection
export const updateWebSocketMessageHandler = (onMessage: (data: any) => void) => {
  wsMessageHandler = onMessage;
  return wsConnection;
};

const agentService = {
  checkAgentHealth,
  getPortfolioData,
  getTradingSignals,
  getActiveStrategies,
  getMarketData,
  executeTask,
  getTaskStatus,
  getSystemIntelligence,
  createWebSocketConnection,
  closeWebSocketConnection,
  updateWebSocketMessageHandler,
};

export default agentService;
