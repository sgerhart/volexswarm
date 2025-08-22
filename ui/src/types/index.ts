// Core types for VolexSwarm Agentic Trading System

// Portfolio and Investment Types
export interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  totalValue: number;
  unrealizedPnL: number;
  realizedPnL: number;
  allocation: number; // Percentage of portfolio
}

export interface PortfolioData {
  totalValue: number;
  unrealizedPnL: number;
  realizedPnL: number;
  positions: Position[];
  performance: PerformanceMetrics;
  timestamp: string;
}

export interface PerformanceMetrics {
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

// Agent Intelligence Types
export interface AgentIntelligence {
  agentName: string;
  status: 'healthy' | 'warning' | 'error';
  currentTask: string;
  capabilities: string[];
  performance: AgentPerformance;
  autonomousDecisions: AutonomousDecision[];
  port: number;
  endpoint: string;
}

export interface AgentPerformance {
  tasksCompleted: number;
  successRate: number;
  avgResponseTime: number;
  lastActive: string;
  uptime: string;
}

export interface AutonomousDecision {
  id: string;
  timestamp: string;
  agentName: string;
  decisionType: string;
  reasoning: string;
  outcome: 'success' | 'failure' | 'pending';
  confidence: number;
  metadata: Record<string, any>;
}

// Trading Intelligence Types
export interface TradingSignal {
  id: string;
  symbol: string;
  signalType: 'buy' | 'sell' | 'hold';
  strength: number; // 0-1
  confidence: number; // 0-1
  timeframe: string;
  indicators: Record<string, number>;
  timestamp: string;
  agentName: string;
}

export interface ProductionStrategy {
  id: string;
  name: string;
  type: string;
  symbol: string;
  timeframe: string;
  status: 'active' | 'paused' | 'inactive' | 'deactivated';
  performance: PerformanceMetrics;
  riskProfile: string;
  allocation: Record<string, any>;
  riskLimits: Record<string, any>;
  parameters: Record<string, any>;
}

// MCP Tool Types
export interface MCPTool {
  name: string;
  description: string;
  category: string;
  requiredPermissions: string[];
  parameters: Record<string, any>;
}

export interface MCPToolRegistry {
  tools: MCPTool[];
  categories: string[];
  permissions: string[];
}

// Real-time Data Types
export interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  change: number;
  changePercent: number;
  timestamp: string;
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  agentName?: string;
}

// API Response Types
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message?: string;
  timestamp: string;
}

// UI State Types
export interface UIState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  selectedTimeframe: string;
  selectedSymbol: string;
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: string;
  read: boolean;
}

// Chart and Visualization Types
export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface TimeframeOption {
  value: string;
  label: string;
  interval: string;
}

// Agent Communication Types
export interface AgentTask {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  assignedAgents: string[];
  progress: number;
  result?: any;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AgentWorkflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  status: 'active' | 'paused' | 'completed' | 'failed';
  currentStep: number;
  progress: number;
}

export interface WorkflowStep {
  id: string;
  name: string;
  agentName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  dependencies: string[];
  result?: any;
  error?: string;
}
