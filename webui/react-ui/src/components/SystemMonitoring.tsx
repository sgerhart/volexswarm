import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  NetworkCheck as NetworkIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface SystemMetric {
  name: string;
  value: number;
  unit: string;
  status: 'normal' | 'warning' | 'critical';
  threshold: number;
}

interface Alert {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string;
  source: string;
  acknowledged: boolean;
}

interface PerformanceData {
  timestamp: string;
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

const SystemMonitoring: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetric[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [alertDialog, setAlertDialog] = useState(false);

  useEffect(() => {
    // Simulate real-time system metrics
    const mockMetrics: SystemMetric[] = [
      {
        name: 'CPU Usage',
        value: 45.2,
        unit: '%',
        status: 'normal',
        threshold: 80,
      },
      {
        name: 'Memory Usage',
        value: 67.8,
        unit: '%',
        status: 'warning',
        threshold: 70,
      },
      {
        name: 'Disk Usage',
        value: 23.4,
        unit: '%',
        status: 'normal',
        threshold: 85,
      },
      {
        name: 'Network I/O',
        value: 12.3,
        unit: 'MB/s',
        status: 'normal',
        threshold: 100,
      },
      {
        name: 'Database Connections',
        value: 15,
        unit: '',
        status: 'normal',
        threshold: 50,
      },
      {
        name: 'Active Agents',
        value: 8,
        unit: '',
        status: 'normal',
        threshold: 10,
      },
    ];

    const mockAlerts: Alert[] = [
      {
        id: '1',
        level: 'warning',
        message: 'Memory usage is approaching threshold (67.8%)',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        source: 'System Monitor',
        acknowledged: false,
      },
      {
        id: '2',
        level: 'info',
        message: 'Strategy agent restarted successfully',
        timestamp: new Date(Date.now() - 600000).toISOString(),
        source: 'Agent Manager',
        acknowledged: true,
      },
      {
        id: '3',
        level: 'error',
        message: 'Failed to connect to external API endpoint',
        timestamp: new Date(Date.now() - 900000).toISOString(),
        source: 'Research Agent',
        acknowledged: false,
      },
    ];

    const mockPerformanceData: PerformanceData[] = Array.from({ length: 24 }, (_, i) => ({
      timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
      cpu: Math.random() * 60 + 20,
      memory: Math.random() * 40 + 50,
      disk: Math.random() * 20 + 20,
      network: Math.random() * 20 + 5,
    }));

    setMetrics(mockMetrics);
    setAlerts(mockAlerts);
    setPerformanceData(mockPerformanceData);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <InfoIcon color="info" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'critical':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon />;
    }
  };

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'info':
        return 'info';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleAcknowledgeAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    ));
  };

  const handleViewAlert = (alert: Alert) => {
    setSelectedAlert(alert);
    setAlertDialog(true);
  };

  const getProgressColor = (value: number, threshold: number) => {
    const percentage = (value / threshold) * 100;
    if (percentage >= 90) return 'error';
    if (percentage >= 70) return 'warning';
    return 'success';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ color: 'primary.main' }}>
          System Monitoring
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => window.location.reload()}
        >
          Refresh
        </Button>
      </Box>

      {/* System Overview */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        {metrics.slice(0, 4).map((metric) => (
          <Card key={metric.name} sx={{ flex: 1, minWidth: 200 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                {metric.name.includes('CPU') && <SpeedIcon color="primary" />}
                {metric.name.includes('Memory') && <MemoryIcon color="primary" />}
                {metric.name.includes('Disk') && <StorageIcon color="primary" />}
                {metric.name.includes('Network') && <NetworkIcon color="primary" />}
                <Typography color="textSecondary" variant="body2">
                  {metric.name}
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ color: 'primary.main' }}>
                {metric.value}{metric.unit}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={(metric.value / metric.threshold) * 100}
                  color={getProgressColor(metric.value, metric.threshold) as any}
                  sx={{ flex: 1 }}
                />
                <Chip
                  label={metric.status}
                  color={getStatusColor(metric.status) as any}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>

      {/* Alerts and Performance */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {/* Alerts Panel */}
        <Card sx={{ flex: 2, minWidth: 400 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">System Alerts</Typography>
              <Chip
                label={`${alerts.filter(a => !a.acknowledged).length} Active`}
                color="warning"
                size="small"
              />
            </Box>
            <List>
              {alerts.slice(0, 5).map((alert) => (
                <ListItem
                  key={alert.id}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    backgroundColor: alert.acknowledged ? 'action.hover' : 'background.paper',
                  }}
                >
                  <ListItemIcon>
                    {getAlertIcon(alert.level)}
                  </ListItemIcon>
                  <ListItemText
                    primary={alert.message}
                    secondary={`${alert.source} • ${new Date(alert.timestamp).toLocaleString()}`}
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {!alert.acknowledged && (
                      <Button
                        size="small"
                        onClick={() => handleAcknowledgeAlert(alert.id)}
                      >
                        Acknowledge
                      </Button>
                    )}
                    <Button
                      size="small"
                      onClick={() => handleViewAlert(alert)}
                    >
                      View
                    </Button>
                  </Box>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>

        {/* Performance History */}
        <Card sx={{ flex: 1, minWidth: 300 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance History (24h)
            </Typography>
            <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Time</TableCell>
                    <TableCell>CPU</TableCell>
                    <TableCell>Memory</TableCell>
                    <TableCell>Disk</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {performanceData.slice(-6).map((data, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        {new Date(data.timestamp).toLocaleTimeString()}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="textSecondary">
                          {data.cpu.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="textSecondary">
                          {data.memory.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="textSecondary">
                          {data.disk.toFixed(1)}%
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Box>

      {/* Detailed Metrics */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Detailed System Metrics
          </Typography>
          <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Metric</TableCell>
                  <TableCell>Current Value</TableCell>
                  <TableCell>Threshold</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Trend</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {metrics.map((metric) => (
                  <TableRow key={metric.name} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {metric.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {metric.value}{metric.unit}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {metric.threshold}{metric.unit}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={metric.status}
                        color={getStatusColor(metric.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <LinearProgress
                        variant="determinate"
                        value={(metric.value / metric.threshold) * 100}
                        color={getProgressColor(metric.value, metric.threshold) as any}
                        sx={{ width: 100 }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Alert Details Dialog */}
      <Dialog open={alertDialog} onClose={() => setAlertDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Alert Details
        </DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box>
              <Alert severity={getAlertColor(selectedAlert.level) as any} sx={{ mb: 2 }}>
                {selectedAlert.message}
              </Alert>
              <Typography variant="body2" color="textSecondary">
                <strong>Source:</strong> {selectedAlert.source}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                <strong>Time:</strong> {new Date(selectedAlert.timestamp).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                <strong>Status:</strong> {selectedAlert.acknowledged ? 'Acknowledged' : 'Active'}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAlertDialog(false)}>Close</Button>
          {selectedAlert && !selectedAlert.acknowledged && (
            <Button
              onClick={() => {
                handleAcknowledgeAlert(selectedAlert.id);
                setAlertDialog(false);
              }}
              variant="contained"
            >
              Acknowledge
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SystemMonitoring; 