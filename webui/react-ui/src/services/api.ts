import axios from 'axios';

// API base URL - will be different in production vs development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8005';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Agent health check endpoints - updated to match actual docker-compose ports
const agentEndpoints = {
  research: 'http://localhost:8001/health',
  execution: 'http://localhost:8002/health',
  signal: 'http://localhost:8003/health',
  meta: 'http://localhost:8004/health',
  // Additional agents (not yet in docker-compose)
  optimize: 'http://localhost:8006/health',
  monitor: 'http://localhost:8007/health',
  backtest: 'http://localhost:8008/health',
  compliance: 'http://localhost:8009/health',
  risk: 'http://localhost:8010/health',
  strategy: 'http://localhost:8011/health',
};

// API functions
export const apiService = {
  // Get system status
  async getSystemStatus() {
    try {
      const response = await api.get('/status');
      return response.data;
    } catch (error) {
      console.error('Failed to get system status:', error);
      return { status: 'unknown', agents: [] };
    }
  },

  // Get agent health status
  async getAgentHealth(agentName: string) {
    try {
      const endpoint = agentEndpoints[agentName as keyof typeof agentEndpoints];
      if (!endpoint) {
        throw new Error(`Unknown agent: ${agentName}`);
      }
      
      const response = await axios.get(endpoint, { timeout: 5000 });
      return {
        name: agentName,
        status: 'healthy',
        lastSeen: new Date().toISOString(),
        endpoint,
        data: response.data,
      };
    } catch (error) {
      return {
        name: agentName,
        status: 'unhealthy',
        lastSeen: new Date().toISOString(),
        endpoint: agentEndpoints[agentName as keyof typeof agentEndpoints] || '',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  },

  // Get all agents health
  async getAllAgentsHealth() {
    const agents = Object.keys(agentEndpoints);
    const healthPromises = agents.map(agent => this.getAgentHealth(agent));
    
    try {
      const results = await Promise.allSettled(healthPromises);
      return results.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value;
        } else {
          return {
            name: agents[index],
            status: 'unknown',
            lastSeen: new Date().toISOString(),
            endpoint: agentEndpoints[agents[index] as keyof typeof agentEndpoints] || '',
            error: result.reason?.message || 'Unknown error',
          };
        }
      });
    } catch (error) {
      console.error('Failed to get agents health:', error);
      return [];
    }
  },

  // Get system metrics
  async getSystemMetrics() {
    try {
      const response = await api.get('/metrics');
      return response.data;
    } catch (error) {
      console.error('Failed to get system metrics:', error);
      return {
        cpu: 0,
        memory: 0,
        disk: 0,
        network: 0,
      };
    }
  },

  // Get trading data
  async getTradingData() {
    try {
      const response = await api.get('/trading');
      return response.data;
    } catch (error) {
      console.error('Failed to get trading data:', error);
      return {
        portfolioValue: 0,
        dailyPnL: 0,
        totalPnL: 0,
        activePositions: 0,
        recentTrades: [],
      };
    }
  },

  // Get agent logs
  async getAgentLogs(agentName?: string, limit = 100) {
    try {
      const params = new URLSearchParams();
      if (agentName) params.append('agent', agentName);
      params.append('limit', limit.toString());
      
      const response = await api.get(`/logs?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get agent logs:', error);
      return [];
    }
  },

  // Refresh data
  async refreshData() {
    try {
      const [systemStatus, agentsHealth, metrics, tradingData] = await Promise.allSettled([
        this.getSystemStatus(),
        this.getAllAgentsHealth(),
        this.getSystemMetrics(),
        this.getTradingData(),
      ]);

      return {
        systemStatus: systemStatus.status === 'fulfilled' ? systemStatus.value : null,
        agentsHealth: agentsHealth.status === 'fulfilled' ? agentsHealth.value : [],
        metrics: metrics.status === 'fulfilled' ? metrics.value : null,
        tradingData: tradingData.status === 'fulfilled' ? tradingData.value : null,
      };
    } catch (error) {
      console.error('Failed to refresh data:', error);
      return {
        systemStatus: null,
        agentsHealth: [],
        metrics: null,
        tradingData: null,
      };
    }
  },
};

export default apiService; 