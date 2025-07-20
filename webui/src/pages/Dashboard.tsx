import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Psychology,
  AccountBalance,
  ShowChart,
  Refresh,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { format } from 'date-fns';
import {
  getSystemStatus,
  getSignals,
  getMarketData,
  getTrades,
  refreshData,
} from '../api/system';
import { toast } from 'react-hot-toast';

const Dashboard: React.FC = () => {
  const { data: systemStatus, refetch: refetchSystem } = useQuery('systemStatus', getSystemStatus);
  const { data: signals } = useQuery('signals', getSignals);
  const { data: marketData } = useQuery('marketData', getMarketData);
  const { data: trades } = useQuery('trades', getTrades);

  const handleRefresh = async () => {
    try {
      await refreshData();
      refetchSystem();
      toast.success('Data refreshed successfully');
    } catch (error) {
      toast.error('Failed to refresh data');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'success';
      case 'degraded':
        return 'warning';
      default:
        return 'error';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircle />;
      case 'degraded':
        return <Warning />;
      default:
        return <Error />;
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>
          VolexSwarm Dashboard
        </Typography>
        <Tooltip title="Refresh Data">
          <IconButton onClick={handleRefresh} color="primary">
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {/* System Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            {systemStatus && getStatusIcon(systemStatus.status)}
            <Typography variant="h6">System Status</Typography>
            {systemStatus && (
              <Chip
                label={systemStatus.status}
                color={getStatusColor(systemStatus.status)}
                variant="outlined"
              />
            )}
          </Box>
          {systemStatus?.metrics && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Agents Online
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {systemStatus.metrics.healthy_agents}/{systemStatus.metrics.total_agents}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(systemStatus.metrics.healthy_agents / systemStatus.metrics.total_agents) * 100}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Active Signals
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {systemStatus.metrics.active_signals}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Trades
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {systemStatus.metrics.total_trades}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    System Uptime
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {systemStatus.metrics.system_uptime}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          )}
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Recent Signals */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp />
                Recent Signals
              </Typography>
              {signals && signals.length > 0 ? (
                <Box>
                  {signals.slice(0, 5).map((signal, index) => (
                    <Box
                      key={index}
                      sx={{
                        p: 2,
                        mb: 1,
                        border: '1px solid #333',
                        borderRadius: 1,
                        backgroundColor: signal.signal_type === 'BUY' ? 'rgba(0, 212, 170, 0.1)' : 'rgba(255, 107, 53, 0.1)',
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {signal.symbol}
                        </Typography>
                        <Chip
                          label={signal.signal_type}
                          color={signal.signal_type === 'BUY' ? 'success' : 'error'}
                          size="small"
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Confidence: {signal.confidence.toFixed(1)}% | Strength: {signal.strength.toFixed(1)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {format(new Date(signal.timestamp), 'MMM dd, HH:mm')}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">No recent signals</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Market Overview */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <ShowChart />
                Market Overview
              </Typography>
              {marketData && Object.keys(marketData).length > 0 ? (
                <Box>
                  {Object.entries(marketData).slice(0, 5).map(([symbol, data]) => (
                    <Box
                      key={symbol}
                      sx={{
                        p: 2,
                        mb: 1,
                        border: '1px solid #333',
                        borderRadius: 1,
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {symbol}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {data.change_24h >= 0 ? <TrendingUp color="success" /> : <TrendingDown color="error" />}
                          <Typography
                            variant="body2"
                            color={data.change_24h >= 0 ? 'success.main' : 'error.main'}
                          >
                            {formatPercentage(data.change_24h)}
                          </Typography>
                        </Box>
                      </Box>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {formatCurrency(data.price)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Vol: {new Intl.NumberFormat().format(data.volume_24h)}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">No market data available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Trades */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <AccountBalance />
                Recent Trades
              </Typography>
              {trades && trades.length > 0 ? (
                <Box>
                  {trades.slice(0, 10).map((trade, index) => (
                    <Box
                      key={index}
                      sx={{
                        p: 2,
                        mb: 1,
                        border: '1px solid #333',
                        borderRadius: 1,
                        backgroundColor: trade.side === 'BUY' ? 'rgba(0, 212, 170, 0.1)' : 'rgba(255, 107, 53, 0.1)',
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {trade.symbol}
                        </Typography>
                        <Chip
                          label={trade.side}
                          color={trade.side === 'BUY' ? 'success' : 'error'}
                          size="small"
                        />
                      </Box>
                      <Typography variant="body2">
                        {trade.quantity} @ {formatCurrency(trade.price)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {format(new Date(trade.timestamp), 'MMM dd, HH:mm:ss')}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">No recent trades</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 