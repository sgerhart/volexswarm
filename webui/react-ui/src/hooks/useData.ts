import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';

// Query keys
export const queryKeys = {
  systemStatus: ['systemStatus'],
  agentsHealth: ['agentsHealth'],
  systemMetrics: ['systemMetrics'],
  tradingData: ['tradingData'],
  agentLogs: (agentName?: string) => ['agentLogs', agentName],
  allData: ['allData'],
};

// Custom hook for system status
export const useSystemStatus = () => {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: apiService.getSystemStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  });
};

// Custom hook for agents health
export const useAgentsHealth = () => {
  return useQuery({
    queryKey: queryKeys.agentsHealth,
    queryFn: apiService.getAllAgentsHealth,
    refetchInterval: 15000, // Refetch every 15 seconds
    staleTime: 5000, // Consider data stale after 5 seconds
  });
};

// Custom hook for system metrics
export const useSystemMetrics = () => {
  return useQuery({
    queryKey: queryKeys.systemMetrics,
    queryFn: apiService.getSystemMetrics,
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000,
  });
};

// Custom hook for trading data
export const useTradingData = () => {
  return useQuery({
    queryKey: queryKeys.tradingData,
    queryFn: apiService.getTradingData,
    refetchInterval: 5000, // Refetch every 5 seconds
    staleTime: 2000,
  });
};

// Custom hook for agent logs
export const useAgentLogs = (agentName?: string, limit = 100) => {
  return useQuery({
    queryKey: queryKeys.agentLogs(agentName),
    queryFn: () => apiService.getAgentLogs(agentName, limit),
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000,
  });
};

// Custom hook for all data
export const useAllData = () => {
  return useQuery({
    queryKey: queryKeys.allData,
    queryFn: apiService.refreshData,
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 15000,
  });
};

// Custom hook for manual refresh
export const useRefreshData = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiService.refreshData,
    onSuccess: (data) => {
      // Update all related queries with fresh data
      queryClient.setQueryData(queryKeys.systemStatus, data.systemStatus);
      queryClient.setQueryData(queryKeys.agentsHealth, data.agentsHealth);
      queryClient.setQueryData(queryKeys.systemMetrics, data.metrics);
      queryClient.setQueryData(queryKeys.tradingData, data.tradingData);
      
      // Invalidate queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.systemStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.agentsHealth });
      queryClient.invalidateQueries({ queryKey: queryKeys.systemMetrics });
      queryClient.invalidateQueries({ queryKey: queryKeys.tradingData });
    },
  });
};

// Custom hook for individual agent health
export const useAgentHealth = (agentName: string) => {
  return useQuery({
    queryKey: ['agentHealth', agentName],
    queryFn: () => apiService.getAgentHealth(agentName),
    refetchInterval: 10000, // Refetch every 10 seconds
    staleTime: 5000,
  });
};

// Utility hook for real-time updates
export const useRealTimeUpdates = () => {
  const queryClient = useQueryClient();
  
  // Set up WebSocket connection for real-time updates
  // This is a placeholder for future WebSocket implementation
  const setupWebSocket = () => {
    // TODO: Implement WebSocket connection
    // const ws = new WebSocket('ws://localhost:8005/ws');
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data);
    //   queryClient.setQueryData(queryKeys.allData, data);
    // };
  };
  
  return {
    setupWebSocket,
  };
}; 