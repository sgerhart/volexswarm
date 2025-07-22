import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as CpuIcon,
  NetworkCheck as NetworkIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Wifi as ConnectedIcon,
  WifiOff as DisconnectedIcon,
  Sync as SyncIcon,
} from '@mui/icons-material';
import { 
  useSystemMetrics, 
  useWebSocketConnection,
  useRealTimeData 
} from '../hooks/useWebSocket';
import { fetchSystemMetrics } from '../services/systemService';

const SystemMetrics: React.FC = () => {
  // Real-time WebSocket connection status
  const { isConnected, isReconnecting, connectionId } = useWebSocketConnection();
  
  // Real-time system metrics with HTTP fallback
  const { 
    data: systemMetrics, 
    loading: metricsLoading, 
    error: metricsError,
    source: metricsSource,
    isRealTime: metricsRealTime
  } = useRealTimeData(
    'system_metrics',
    fetchSystemMetrics,
    15000 // 15 second polling fallback
  );

  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    setLastUpdated(new Date());
  }, [systemMetrics]);

  const getProgressColor = (value: number): "primary" | "secondary" | "error" | "warning" | "info" | "success" => {
    if (value >= 90) return 'error';
    if (value >= 70) return 'warning';
    if (value >= 50) return 'info';
    return 'success';
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleRefresh = () => {
    setLastUpdated(new Date());
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ color: 'primary.main' }}>
          System Metrics - WebSocket Test
        </Typography>
        
        {/* Connection Status Indicator */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            icon={isConnected ? <ConnectedIcon /> : isReconnecting ? <SyncIcon /> : <DisconnectedIcon />}
            label={
              isConnected 
                ? `Real-time (${connectionId?.slice(-8)})` 
                : isReconnecting 
                  ? 'Reconnecting...' 
                  : 'Offline'
            }
            color={isConnected ? 'success' : isReconnecting ? 'warning' : 'error'}
            size="small"
          />
          
          <Chip
            label={metricsRealTime ? 'Live Data' : 'Polling Mode'}
            color={metricsRealTime ? 'primary' : 'secondary'}
            size="small"
          />
          
          <IconButton onClick={handleRefresh} disabled={metricsLoading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Error Display */}
      {metricsError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Metrics: {metricsError}
        </Alert>
      )}

      {/* System Metrics Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
        
        {/* CPU Usage */}
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CpuIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">CPU Usage</Typography>
              {metricsRealTime && (
                <TrendingUpIcon color="success" sx={{ ml: 'auto', fontSize: 16 }} />
              )}
            </Box>
            
            {metricsLoading ? (
              <CircularProgress size={24} />
            ) : (
              <>
                <Typography variant="h4" sx={{ mb: 1, color: 'primary.main' }}>
                  {systemMetrics?.cpu_usage?.toFixed(1) || 0}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={systemMetrics?.cpu_usage || 0}
                  color={getProgressColor(systemMetrics?.cpu_usage || 0)}
                  sx={{ height: 8, borderRadius: 1 }}
                />
              </>
            )}
          </CardContent>
        </Card>

        {/* Memory Usage */}
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <MemoryIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Memory Usage</Typography>
              {metricsRealTime && (
                <TrendingUpIcon color="success" sx={{ ml: 'auto', fontSize: 16 }} />
              )}
            </Box>
            
            {metricsLoading ? (
              <CircularProgress size={24} />
            ) : (
              <>
                <Typography variant="h4" sx={{ mb: 1, color: 'primary.main' }}>
                  {systemMetrics?.memory_usage?.toFixed(1) || 0}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={systemMetrics?.memory_usage || 0}
                  color={getProgressColor(systemMetrics?.memory_usage || 0)}
                  sx={{ height: 8, borderRadius: 1 }}
                />
              </>
            )}
          </CardContent>
        </Card>

        {/* Disk Usage */}
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <StorageIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Disk Usage</Typography>
              {metricsRealTime && (
                <TrendingUpIcon color="success" sx={{ ml: 'auto', fontSize: 16 }} />
              )}
            </Box>
            
            {metricsLoading ? (
              <CircularProgress size={24} />
            ) : (
              <>
                <Typography variant="h4" sx={{ mb: 1, color: 'primary.main' }}>
                  {systemMetrics?.disk_usage?.toFixed(1) || 0}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={systemMetrics?.disk_usage || 0}
                  color={getProgressColor(systemMetrics?.disk_usage || 0)}
                  sx={{ height: 8, borderRadius: 1 }}
                />
              </>
            )}
          </CardContent>
        </Card>

        {/* Network I/O */}
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <NetworkIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Network I/O</Typography>
              {metricsRealTime && (
                <TrendingUpIcon color="success" sx={{ ml: 'auto', fontSize: 16 }} />
              )}
            </Box>
            
            {metricsLoading ? (
              <CircularProgress size={24} />
            ) : (
              <Box>
                <Typography variant="body2" color="textSecondary">
                  In: {formatBytes(systemMetrics?.network_io?.bytes_recv || 0)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Out: {formatBytes(systemMetrics?.network_io?.bytes_sent || 0)}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  Active: {(systemMetrics as any)?.active_connections || 0}
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* WebSocket Test Status */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            🧪 Phase 2.6 WebSocket Test Results
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
            <Box>
              <Typography variant="body2" color="textSecondary">WebSocket Connection</Typography>
              <Typography variant="h6" color={isConnected ? 'success.main' : 'error.main'}>
                {isConnected ? '✅ Connected' : '❌ Disconnected'}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="textSecondary">Connection ID</Typography>
              <Typography variant="body1">
                {connectionId || 'None'}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="textSecondary">Data Source</Typography>
              <Typography variant="h6" color={metricsRealTime ? 'primary.main' : 'secondary.main'}>
                {metricsSource === 'websocket' ? '🔄 WebSocket' : '📡 HTTP Polling'}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="textSecondary">Real-Time Status</Typography>
              <Typography variant="h6" color={metricsRealTime ? 'success.main' : 'warning.main'}>
                {metricsRealTime ? '⚡ Live Data' : '🔄 Fallback Mode'}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Status Footer */}
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="textSecondary">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </Typography>
        
        <Typography variant="body2" color="textSecondary">
          Data source: {metricsSource === 'websocket' ? 'Real-time WebSocket' : 'HTTP Polling'}
          {metricsRealTime && ' • Live updates every 5s'}
        </Typography>
      </Box>
    </Box>
  );
};

export default SystemMetrics; 