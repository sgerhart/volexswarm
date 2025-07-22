/**
 * React Hooks for WebSocket Integration
 * Provides easy-to-use hooks for real-time data in React components
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import webSocketService, { 
  WebSocketMessage, 
  ConnectionStatus 
} from '../services/websocketService';

/**
 * Hook for managing WebSocket connection status
 */
export const useWebSocketConnection = () => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(
    webSocketService.getConnectionStatus()
  );

  useEffect(() => {
    const unsubscribe = webSocketService.onConnectionChange(setConnectionStatus);
    return unsubscribe;
  }, []);

  const connect = useCallback(() => {
    return webSocketService.connect();
  }, []);

  const disconnect = useCallback(() => {
    webSocketService.disconnect();
  }, []);

  return {
    connectionStatus,
    connect,
    disconnect,
    isConnected: connectionStatus.connected,
    isReconnecting: connectionStatus.reconnecting,
    connectionId: connectionStatus.connectionId,
    error: connectionStatus.error
  };
};

/**
 * Hook for subscribing to real-time data topics
 */
export const useWebSocketSubscription = <T = any>(
  topic: string,
  initialData?: T
) => {
  const [data, setData] = useState<T | undefined>(initialData);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isSubscribed = true;
    setLoading(true);
    setError(null);

    const handleMessage = (message: WebSocketMessage) => {
      if (!isSubscribed) return;
      
      try {
        setLastMessage(message);
        setData(message.data);
        setLoading(false);
        setError(null);
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    const unsubscribe = webSocketService.subscribe(topic, handleMessage);

    // Initial load complete after a short delay if no data received
    const timeoutId = setTimeout(() => {
      if (isSubscribed && loading) {
        setLoading(false);
      }
    }, 2000);

    return () => {
      isSubscribed = false;
      clearTimeout(timeoutId);
      unsubscribe();
    };
  }, [topic, loading]);

  return {
    data,
    lastMessage,
    loading,
    error,
    isSubscribed: true
  };
};

/**
 * Hook for agent status updates
 */
export const useAgentStatus = () => {
  return useWebSocketSubscription('agent_status', {
    status: 'unknown',
    agents: {},
    timestamp: new Date().toISOString()
  });
};

/**
 * Hook for system metrics
 */
export const useSystemMetrics = () => {
  return useWebSocketSubscription('system_metrics', {
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    network_io: { in: 0, out: 0 },
    active_connections: 0,
    timestamp: new Date().toISOString()
  });
};

/**
 * Hook for trade updates
 */
export const useTradeUpdates = () => {
  const [trades, setTrades] = useState<any[]>([]);
  
  const { data, lastMessage } = useWebSocketSubscription('trade_updates');

  useEffect(() => {
    if (data) {
      setTrades(prev => [data, ...prev.slice(0, 99)]); // Keep last 100 trades
    }
  }, [data]);

  return {
    trades,
    latestTrade: data,
    lastMessage
  };
};

/**
 * Hook for task progress updates
 */
export const useTaskProgress = () => {
  const [tasks, setTasks] = useState<Map<string, any>>(new Map());
  
  const { data, lastMessage } = useWebSocketSubscription('task_progress');

  useEffect(() => {
    if (data && data.monitor_id) {
      setTasks(prev => {
        const updated = new Map(prev);
        updated.set(data.monitor_id, data);
        return updated;
      });
    }
  }, [data]);

  return {
    tasks: Array.from(tasks.values()),
    latestUpdate: data,
    lastMessage
  };
};

/**
 * Hook for notifications
 */
export const useNotifications = () => {
  const [notifications, setNotifications] = useState<any[]>([]);
  
  const { data, lastMessage } = useWebSocketSubscription('notifications');

  useEffect(() => {
    if (data) {
      setNotifications(prev => [
        { ...data, id: Date.now(), read: false },
        ...prev.slice(0, 49) // Keep last 50 notifications
      ]);
    }
  }, [data]);

  const markAsRead = useCallback((id: number) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, read: true } : notif
      )
    );
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    unreadCount: notifications.filter(n => !n.read).length,
    latestNotification: data,
    markAsRead,
    clearAll,
    lastMessage
  };
};

/**
 * Hook for sending commands via WebSocket
 */
export const useWebSocketCommand = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<any>(null);

  const sendCommand = useCallback(async (command: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await webSocketService.sendCommand(command);
      setLastResponse(response);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Command failed';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    sendCommand,
    loading,
    error,
    lastResponse
  };
};

/**
 * Hook for real-time data with automatic fallback to HTTP
 */
export const useRealTimeData = <T>(
  topic: string,
  httpFallback: () => Promise<T>,
  pollInterval = 10000,
  initialData?: T
) => {
  const [data, setData] = useState<T | undefined>(initialData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<'websocket' | 'http'>('websocket');
  
  const { connectionStatus } = useWebSocketConnection();
  const { data: wsData, error: wsError } = useWebSocketSubscription<T>(topic);
  
  const httpFallbackRef = useRef(httpFallback);
  httpFallbackRef.current = httpFallback;

  // Use WebSocket data when connected
  useEffect(() => {
    if (connectionStatus.connected && wsData) {
      setData(wsData);
      setSource('websocket');
      setLoading(false);
      setError(null);
    }
  }, [connectionStatus.connected, wsData]);

  // Fallback to HTTP polling when WebSocket is not available
  useEffect(() => {
    if (!connectionStatus.connected) {
      setSource('http');
      
      const fetchData = async () => {
        try {
          setLoading(true);
          const result = await httpFallbackRef.current();
          setData(result);
          setError(null);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to fetch data');
        } finally {
          setLoading(false);
        }
      };

      // Initial fetch
      fetchData();

      // Set up polling
      const interval = setInterval(fetchData, pollInterval);
      
      return () => clearInterval(interval);
    }
  }, [connectionStatus.connected, pollInterval]);

  return {
    data,
    loading,
    error: error || wsError,
    source,
    isRealTime: source === 'websocket' && connectionStatus.connected
  };
};

/**
 * Hook for WebSocket connection statistics
 */
export const useWebSocketStats = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const result = await webSocketService.getConnectionStats();
      setStats(result);
    } catch (error) {
      console.error('Failed to fetch WebSocket stats:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  return {
    stats,
    loading,
    refresh: fetchStats
  };
}; 