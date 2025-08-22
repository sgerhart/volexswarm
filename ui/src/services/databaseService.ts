import axios from 'axios';

// Database service for direct queries to VolexSwarm database
// Note: For now, we'll use agent endpoints since direct DB access isn't configured

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

export interface Trade {
  trade_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  executed_at: string;
  strategy_id?: number;
}

export interface PerformanceMetrics {
  strategy_id?: number;
  date: string;
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
}

class DatabaseService {
  private baseURL: string;

  constructor() {
    // For now, we'll use the agent endpoints since direct DB access isn't configured
    this.baseURL = 'http://localhost:8002'; // Execution Agent
  }

  // Get portfolio positions from the database
  async getPortfolioPositions(): Promise<PortfolioPosition[]> {
    try {
      // Try to get from Execution Agent first
      const response = await axios.get(`${this.baseURL}/api/execution/portfolio`);
      return response.data;
    } catch (error) {
      console.warn('Execution Agent portfolio endpoint not available, using fallback');
      // Fallback: return empty portfolio for now
      return [];
    }
  }

  // Get recent trades
  async getRecentTrades(limit: number = 50): Promise<Trade[]> {
    try {
      const response = await axios.get(`${this.baseURL}/api/execution/trades?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.warn('Execution Agent trades endpoint not available, using fallback');
      return [];
    }
  }

  // Get performance metrics
  async getPerformanceMetrics(): Promise<PerformanceMetrics[]> {
    try {
      const response = await axios.get(`${this.baseURL}/api/execution/performance`);
      return response.data;
    } catch (error) {
      console.warn('Execution Agent performance endpoint not available, using fallback');
      return [];
    }
  }

  // Calculate portfolio value from positions
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
}

const databaseService = new DatabaseService();
export default databaseService;
