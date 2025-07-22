import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as CpuIcon,
  NetworkCheck as NetworkIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SystemMetric {
  name: string;
  value: number;
  unit: string;
  color: string;
  icon: React.ReactNode;
}

const SystemMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetric[]>([
    { name: 'CPU Usage', value: 45, unit: '%', color: '#00d4aa', icon: <CpuIcon /> },
    { name: 'Memory Usage', value: 68, unit: '%', color: '#29b6f6', icon: <MemoryIcon /> },
    { name: 'Disk Usage', value: 32, unit: '%', color: '#ffa726', icon: <StorageIcon /> },
    { name: 'Network', value: 12, unit: 'MB/s', color: '#ab47bc', icon: <NetworkIcon /> },
  ]);

  const [chartData, setChartData] = useState([
    { time: '00:00', cpu: 45, memory: 68, disk: 32 },
    { time: '02:00', cpu: 52, memory: 72, disk: 33 },
    { time: '04:00', cpu: 38, memory: 65, disk: 31 },
    { time: '06:00', cpu: 61, memory: 78, disk: 34 },
    { time: '08:00', cpu: 67, memory: 82, disk: 35 },
    { time: '10:00', cpu: 58, memory: 75, disk: 33 },
    { time: '12:00', cpu: 49, memory: 70, disk: 32 },
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate real-time updates
      setMetrics(prev => prev.map(metric => ({
        ...metric,
        value: Math.floor(Math.random() * 100) + 10,
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getMetricColor = (value: number) => {
    if (value < 50) return 'success';
    if (value < 80) return 'warning';
    return 'error';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', mb: 3 }}>
          System Metrics
        </Typography>

        {/* Real-time Metrics */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
          {metrics.map((metric) => (
            <Box key={metric.name} sx={{ textAlign: 'center', minWidth: 120, flex: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                <Box sx={{ color: metric.color }}>
                  {metric.icon}
                </Box>
              </Box>
              <Typography variant="h6" sx={{ color: metric.color, fontWeight: 'bold' }}>
                {metric.value}{metric.unit}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {metric.name}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metric.value}
                color={getMetricColor(metric.value) as any}
                sx={{ mt: 1, height: 4, borderRadius: 2 }}
              />
            </Box>
          ))}
        </Box>

        {/* Performance Chart */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Performance Trends
          </Typography>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="time" stroke="#b0b0b0" />
              <YAxis stroke="#b0b0b0" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #333',
                  borderRadius: 8,
                }}
              />
              <Line
                type="monotone"
                dataKey="cpu"
                stroke="#00d4aa"
                strokeWidth={2}
                dot={{ fill: '#00d4aa' }}
              />
              <Line
                type="monotone"
                dataKey="memory"
                stroke="#29b6f6"
                strokeWidth={2}
                dot={{ fill: '#29b6f6' }}
              />
              <Line
                type="monotone"
                dataKey="disk"
                stroke="#ffa726"
                strokeWidth={2}
                dot={{ fill: '#ffa726' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>

        {/* System Status */}
        <Box sx={{ mt: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label="Database: Online" color="success" size="small" />
          <Chip label="Vault: Online" color="success" size="small" />
          <Chip label="API: Online" color="success" size="small" />
          <Chip label="WebSocket: Active" color="success" size="small" />
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemMetrics; 