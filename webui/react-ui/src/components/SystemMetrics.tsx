import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Grid,
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
import { fetchSystemMetrics, fetchDockerStats, SystemMetrics as SystemMetricsType, DockerStats } from '../services/systemService';

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

  // Separate state for Docker stats (still using HTTP for now)
  const [dockerStats, setDockerStats] = useState<DockerStats | null>(null);
  const [dockerLoading, setDockerLoading] = useState(false);
  const [dockerError, setDockerError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch Docker stats separately (can be enhanced to WebSocket later)
  const fetchDockerData = async () => {
    try {
      setDockerLoading(true);
      setDockerError(null);
      const docker = await fetchDockerStats();
      setDockerStats(docker);
      setLastUpdated(new Date());
    } catch (err) {
      setDockerError('Failed to fetch Docker stats');
      console.error('Error fetching Docker stats:', err);
    } finally {
      setDockerLoading(false);
    }
  };

  useEffect(() => {
    fetchDockerData();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchDockerData();
    }, 30000); // Poll Docker stats every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleRefresh = () => {
    fetchDockerData();
  };

  const handleToggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
  };

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

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ color: 'primary.main' }}>
          System Metrics
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
          
          <Button
            variant="outlined"
            size="small"
            onClick={handleToggleAutoRefresh}
            color={autoRefresh ? 'primary' : 'secondary'}
          >
            {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
          </Button>
          
          <IconButton onClick={handleRefresh} disabled={metricsLoading || dockerLoading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Error Display */}
      {(metricsError || dockerError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {metricsError && `Metrics: ${metricsError}`}
          {metricsError && dockerError && ' | '}
          {dockerError && `Docker: ${dockerError}`}
        </Alert>
      )}

      {/* System Metrics Grid */}
      <Grid container spacing={3}>
        {/* CPU Usage */}
        <Grid item xs={12} md={6} lg={3}>
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
        </Grid>

        {/* Memory Usage */}
        <Grid item xs={12} md={6} lg={3}>
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
        </Grid>

        {/* Disk Usage */}
        <Grid item xs={12} md={6} lg={3}>
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
        </Grid>

        {/* Network I/O */}
        <Grid item xs={12} md={6} lg={3}>
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
                      Active: {systemMetrics?.active_connections || 0}
                     </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Docker Stats (if available) */}
        {dockerStats && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Docker Containers
                </Typography>
                
                <Grid container spacing={2}>
                  {dockerStats.containers?.map((container, index) => (
                    <Grid item xs={12} md={6} lg={4} key={index}>
                      <Card variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                          {container.name}
                        </Typography>
                        
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2" color="textSecondary">
                            Status: 
                            <Chip 
                              label={container.status} 
                              size="small" 
                              color={container.status === 'running' ? 'success' : 'error'}
                              sx={{ ml: 1 }}
                            />
                          </Typography>
                        </Box>
                        
                        {container.cpu_percent !== undefined && (
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="body2">
                              CPU: {container.cpu_percent.toFixed(1)}%
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={container.cpu_percent}
                              color={getProgressColor(container.cpu_percent)}
                              size="small"
                            />
                          </Box>
                        )}
                        
                        {container.memory_usage && (
                          <Typography variant="body2" color="textSecondary">
                            Memory: {formatBytes(container.memory_usage)}
                          </Typography>
                        )}
                        
                        {container.uptime && (
                          <Typography variant="body2" color="textSecondary">
                            Uptime: {formatUptime(container.uptime)}
                          </Typography>
                        )}
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

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