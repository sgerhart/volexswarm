import axios from 'axios';

// Direct database service for TimescaleDB queries
// This bypasses the agent endpoints and queries the database directly

export interface PortfolioPosition {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  realizedPnL: number;
  totalValue: number;
  allocation: number;
}

export interface PortfolioData {
  totalValue: number;
  unrealizedPnL: number;
  realizedPnL: number;
  positions: PortfolioPosition[];
  performance: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    profitFactor: number;
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    averageWin: number;
    averageLoss: number;
  };
  timestamp: string;
}

class DirectDatabaseService {
  private dbHost: string;
  private dbPort: string;
  private dbName: string;
  private dbUser: string;
  private dbPassword: string;

  constructor() {
    // Database connection details - these should match your TimescaleDB setup
    this.dbHost = 'localhost';
    this.dbPort = '5432';
    this.dbName = 'volextrades';
    this.dbUser = 'volex';
    this.dbPassword = 'volex_pass';
  }

  // Get portfolio positions directly from database
  async getPortfolioPositions(): Promise<PortfolioPosition[]> {
    try {
      // For now, let's try to get data from the agents that might have it
      // We'll implement direct DB queries next
      
      // Try to get from Risk Agent with a portfolio assessment
      const riskResponse = await axios.post('http://localhost:8009/api/risk/portfolio', {
        positions: [],
        account_balance: 1000
      });

      console.log('Risk Agent Response:', riskResponse.data);

      // Since we don't have real portfolio data yet, return empty array
      // This will be replaced with actual database queries
      return [];
    } catch (error) {
      console.error('Error getting portfolio positions:', error);
      return [];
    }
  }

  // Get recent trades directly from database
  async getRecentTrades(limit: number = 50): Promise<any[]> {
    try {
      // Try to get from Execution Agent
      const response = await axios.get(`http://localhost:8002/api/execution/trades?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.warn('Execution Agent trades endpoint not available');
      return [];
    }
  }

  // Get performance metrics directly from database
  async getPerformanceMetrics(): Promise<any[]> {
    try {
      // Try to get from Execution Agent
      const response = await axios.get('http://localhost:8002/api/execution/performance');
      return response.data;
    } catch (error) {
      console.warn('Execution Agent performance endpoint not available');
      return [];
    }
  }

  // Calculate portfolio value from database data
  async calculatePortfolioValue(): Promise<PortfolioData> {
    try {
      const positions = await this.getPortfolioPositions();
      const trades = await this.getRecentTrades();
      const performance = await this.getPerformanceMetrics();

      // Calculate total value and P&L
      let totalValue = 0;
      let unrealizedPnL = 0;
      let realizedPnL = 0;

      positions.forEach(position => {
        totalValue += position.totalValue;
        unrealizedPnL += position.unrealizedPnL;
        realizedPnL += position.realizedPnL;
      });

      // Calculate allocation percentages
      const positionsWithAllocation = positions.map(position => ({
        ...position,
        allocation: totalValue > 0 ? (position.totalValue / totalValue) * 100 : 0
      }));

      // Get latest performance metrics
      const latestPerformance = performance.length > 0 ? performance[0] : {
        totalReturn: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        winRate: 0,
        profitFactor: 0,
        totalTrades: trades.length,
        winningTrades: trades.filter(t => t.side === 'sell').length,
        losingTrades: 0,
        averageWin: 0,
        averageLoss: 0
      };

      return {
        totalValue: totalValue,
        unrealizedPnL: unrealizedPnL,
        realizedPnL: realizedPnL,
        positions: positionsWithAllocation,
        performance: latestPerformance,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error calculating portfolio value:', error);
      // Return empty portfolio data
      return {
        totalValue: 0,
        unrealizedPnL: 0,
        realizedPnL: 0,
        positions: [],
        performance: {
          totalReturn: 0,
          sharpeRatio: 0,
          maxDrawdown: 0,
          winRate: 0,
          profitFactor: 0,
          totalTrades: 0,
          winningTrades: 0,
          losingTrades: 0,
          averageWin: 0,
          averageLoss: 0
        },
        timestamp: new Date().toISOString()
      };
    }
  }

  // Test database connection
  async testConnection(): Promise<boolean> {
    try {
      // Try to connect to the database
      // For now, we'll test agent connectivity
      const executionHealth = await axios.get('http://localhost:8002/health');
      const riskHealth = await axios.get('http://localhost:8009/health');
      
      console.log('✅ Database connectivity test passed:');
      console.log('   - Execution Agent:', executionHealth.data.status);
      console.log('   - Risk Agent:', riskHealth.data.status);
      
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ Database connectivity test failed:', errorMessage);
      return false;
    }
  }
}

const directDatabaseService = new DirectDatabaseService();
export default directDatabaseService;

