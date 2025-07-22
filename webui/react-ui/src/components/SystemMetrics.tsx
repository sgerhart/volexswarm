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
} from '@mui/icons-material';
import { fetchSystemMetrics, fetchDockerStats, SystemMetrics as SystemMetricsType, DockerStats } from '../services/systemService';

const SystemMetrics: React.FC = () => {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetricsType | null>(null);
  const [dockerStats, setDockerStats] = useState<DockerStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [metrics, docker] = await Promise.all([
        fetchSystemMetrics(),
        fetchDockerStats()
      ]);
      
      setSystemMetrics(metrics);
      setDockerStats(docker);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to fetch system metrics');
      console.error('Error fetching system metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, 15000); // Poll every 15 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleRefresh = () => {
    fetchData();
  };

  const handleToggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (loading && !systemMetrics) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          System Metrics
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Typography variant="caption" color="textSecondary">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
          <Button
            size="small"
            variant={autoRefresh ? 'contained' : 'outlined'}
            onClick={handleToggleAutoRefresh}
          >
            {autoRefresh ? 'Auto Refresh ON' : 'Auto Refresh OFF'}
          </Button>
          <IconButton onClick={handleRefresh} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {systemMetrics && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mb: 4 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography color="textSecondary" gutterBottom>
                  CPU Usage
                </Typography>
                <CpuIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <Typography variant="h4" component="div" sx={{ mb: 1 }}>
                {systemMetrics.cpu_usage.toFixed(1)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={systemMetrics.cpu_usage} 
                sx={{ height: 8, borderRadius: 4 }}
                color={systemMetrics.cpu_usage > 80 ? 'error' : systemMetrics.cpu_usage > 60 ? 'warning' : 'primary'}
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography color="textSecondary" gutterBottom>
                  Memory Usage
                </Typography>
                <MemoryIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <Typography variant="h4" component="div" sx={{ mb: 1 }}>
                {systemMetrics.memory_usage.toFixed(1)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={systemMetrics.memory_usage} 
                sx={{ height: 8, borderRadius: 4 }}
                color={systemMetrics.memory_usage > 80 ? 'error' : systemMetrics.memory_usage > 60 ? 'warning' : 'primary'}
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography color="textSecondary" gutterBottom>
                  Disk Usage
                </Typography>
                <StorageIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <Typography variant="h4" component="div" sx={{ mb: 1 }}>
                {systemMetrics.disk_usage.toFixed(1)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={systemMetrics.disk_usage} 
                sx={{ height: 8, borderRadius: 4 }}
                color={systemMetrics.disk_usage > 80 ? 'error' : systemMetrics.disk_usage > 60 ? 'warning' : 'primary'}
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography color="textSecondary" gutterBottom>
                  System Uptime
                </Typography>
                <TrendingUpIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <Typography variant="h4" component="div">
                {formatUptime(systemMetrics.uptime)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Load: {systemMetrics.load_average.map(l => l.toFixed(2)).join(', ')}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {dockerStats && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Docker Containers
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Chip 
                  label={`Total: ${dockerStats.total_containers}`} 
                  color="primary" 
                  variant="outlined"
                />
                <Chip 
                  label={`Running: ${dockerStats.running_containers}`} 
                  color="success" 
                  variant="outlined"
                />
                <Chip 
                  label={`Stopped: ${dockerStats.stopped_containers}`} 
                  color="error" 
                  variant="outlined"
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    Total Memory
                  </Typography>
                  <Typography variant="h6">
                    {dockerStats.total_memory_usage}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    Total CPU
                  </Typography>
                  <Typography variant="h6">
                    {dockerStats.total_cpu_usage}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Network I/O
              </Typography>
              {systemMetrics && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Bytes Sent
                    </Typography>
                    <Typography variant="h6">
                      {formatBytes(systemMetrics.network_io.bytes_sent)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Bytes Received
                    </Typography>
                    <Typography variant="h6">
                      {formatBytes(systemMetrics.network_io.bytes_recv)}
                    </Typography>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      {dockerStats && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Container Details
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2 }}>
              {dockerStats.containers.map((container) => (
                <Box key={container.id} sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2" fontWeight="bold">
                      {container.name}
                    </Typography>
                    <Chip 
                      label={container.state} 
                      size="small"
                      color={container.state === 'running' ? 'success' : 'error'}
                    />
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                    {container.image}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    {container.memory && (
                      <Chip label={`Memory: ${container.memory}`} size="small" variant="outlined" />
                    )}
                    {container.cpu && (
                      <Chip label={`CPU: ${container.cpu}`} size="small" variant="outlined" />
                    )}
                    <Chip label={`Size: ${container.size}`} size="small" variant="outlined" />
                  </Box>
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                    {container.status}
                  </Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default SystemMetrics; 