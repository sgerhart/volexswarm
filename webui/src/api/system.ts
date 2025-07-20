import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8005/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Types
export interface AgentStatus {
  agent: string;
  status: string;
  healthy: boolean;
  last_check: string;
  details: any;
}

export interface TradingSignal {
  symbol: string;
  signal_type: string;
  confidence: number;
  strength: number;
  timestamp: string;
  price: number;
  indicators: any;
  gpt_commentary?: any;
}

export interface MarketData {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
  timestamp: string;
}

export interface SystemMetrics {
  total_agents: number;
  healthy_agents: number;
  active_signals: number;
  total_trades: number;
  system_uptime: string;
  last_update: string;
}

export interface SystemStatus {
  status: string;
  last_update: string;
  agents: Record<string, any>;
  metrics: SystemMetrics;
}

// API functions
export const getSystemStatus = async (): Promise<SystemStatus> => {
  const response = await api.get('/system-status');
  return response.data;
};

export const getAgents = async (): Promise<Record<string, any>> => {
  const response = await api.get('/agents');
  return response.data;
};

export const getAgent = async (agentName: string): Promise<any> => {
  const response = await api.get(`/agents/${agentName}`);
  return response.data;
};

export const getSignals = async (): Promise<TradingSignal[]> => {
  const response = await api.get('/signals');
  return response.data;
};

export const getMarketData = async (): Promise<Record<string, MarketData>> => {
  const response = await api.get('/market-data');
  return response.data;
};

export const getTrades = async (): Promise<any[]> => {
  const response = await api.get('/trades');
  return response.data;
};

export const getMetrics = async (): Promise<SystemMetrics> => {
  const response = await api.get('/metrics');
  return response.data;
};

export const refreshData = async (): Promise<{ message: string }> => {
  const response = await api.post('/refresh');
  return response.data;
};

export const getHealth = async (): Promise<{ status: string; timestamp: string }> => {
  const response = await api.get('/health');
  return response.data;
}; 