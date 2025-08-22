import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  FormControl,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { getPortfolioHistory } from '../../services/agentService';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface PortfolioChartProps {
  isOpen: boolean;
  onClose: () => void;
  currentPortfolio?: any; // Add current portfolio data
}

interface ChartDataPoint {
  timestamp: string;
  portfolio_value: number;
  total_return_percentage: number;
  usdt_balance: number;
  btc_balance: number;
}

const PortfolioChart: React.FC<PortfolioChartProps> = ({ isOpen, onClose, currentPortfolio }) => {
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(30); // days

  // Debug logging
  console.log('🔍 PortfolioChart: Component rendered');
  console.log('🔍 PortfolioChart: isOpen prop:', isOpen);
  console.log('🔍 PortfolioChart: onClose prop:', onClose);
  
  // Additional debugging for modal state
  useEffect(() => {
    console.log('🔍 PortfolioChart: Modal state changed - isOpen:', isOpen);
    if (isOpen) {
      console.log('🔍 PortfolioChart: Modal should be visible now');
    }
  }, [isOpen]);

  const fetchPortfolioHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const historyData = await getPortfolioHistory(timeRange);
      if (historyData && historyData.length > 0) {
        setChartData(historyData);
      } else {
        // If no history data, create a demo point with current portfolio value
        const btcPosition = currentPortfolio?.positions?.find((p: any) => p.symbol === 'BTC');
        const usdtPosition = currentPortfolio?.positions?.find((p: any) => p.symbol === 'USDT');
        
        setChartData([{
          timestamp: new Date().toISOString(),
          portfolio_value: currentPortfolio?.totalValue || 0,
          total_return_percentage: currentPortfolio?.performance?.totalReturn || 0,
          usdt_balance: usdtPosition?.quantity || 0,
          btc_balance: btcPosition?.quantity || 0
        }]);
      }
    } catch (err) {
      setError('Failed to fetch portfolio history');
      console.error('Error fetching portfolio history:', err);
    } finally {
      setLoading(false);
    }
  }, [timeRange, currentPortfolio]);

  useEffect(() => {
    if (isOpen) {
      fetchPortfolioHistory();
    }
  }, [isOpen, timeRange, fetchPortfolioHistory]);

  if (!isOpen) return null;

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box component="span" sx={{ color: 'white', fontSize: '1.25rem', fontWeight: 600 }}>
          Portfolio Performance Chart
        </Box>
        <Button onClick={onClose} sx={{ color: 'grey.400', '&:hover': { color: 'white' }, fontSize: '1.5rem', fontWeight: 'bold' }}>
          <CloseIcon />
        </Button>
      </DialogTitle>

      <DialogContent>
        {/* Time Range Selector */}
        <Box sx={{ mb: 2 }}>
          <FormControl variant="outlined" sx={{ color: 'white' }}>
            <Typography variant="body2" sx={{ mr: 1, color: 'white' }}>Time Range:</Typography>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              sx={{ bgcolor: 'grey.800', color: 'white' }}
            >
              <MenuItem value={7}>7 Days</MenuItem>
              <MenuItem value={30}>30 Days</MenuItem>
              <MenuItem value={90}>90 Days</MenuItem>
              <MenuItem value={365}>1 Year</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {loading && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <CircularProgress color="primary" />
            <Typography variant="body1" sx={{ color: 'white', mt: 2 }}>Loading portfolio history...</Typography>
          </Box>
        )}

        {!loading && chartData && chartData.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
              Portfolio Value Over Time
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => formatDate(value)}
                  stroke="#888"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#888"
                  fontSize={12}
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#333', 
                    border: '1px solid #555',
                    borderRadius: '8px',
                    color: 'white'
                  }}
                  formatter={(value: any, name: any) => [
                    `$${value.toFixed(2)}`, 
                    name === 'portfolio_value' ? 'Portfolio Value' : name
                  ]}
                  labelFormatter={(label) => formatDate(label)}
                />
                <Area 
                  type="monotone" 
                  dataKey="portfolio_value" 
                  stroke="#8884d8" 
                  fill="#8884d8" 
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        )}

        {!loading && chartData && chartData.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
              Asset Balances Over Time
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => formatDate(value)}
                  stroke="#888"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#888"
                  fontSize={12}
                  yAxisId="left"
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <YAxis 
                  stroke="#888"
                  yAxisId="right"
                  orientation="right"
                  tickFormatter={(value) => value.toFixed(8)}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#333', 
                    border: '1px solid #555',
                    borderRadius: '8px',
                    color: 'white'
                  }}
                  formatter={(value: any, name: any) => {
                    // Determine if this is USDT or BTC based on the name
                    const isUSDT = name === 'usdt_balance' || name === 'USDT Balance';
                    const isBTC = name === 'btc_balance' || name === 'BTC Balance';
                    
                    if (isUSDT) {
                      return [`$${value.toFixed(2)}`, 'USDT Balance'];
                    } else if (isBTC) {
                      return [value.toFixed(8), 'BTC Balance'];
                    } else {
                      // Fallback - try to determine from value range
                      return [value > 100 ? `$${value.toFixed(2)}` : value.toFixed(8), name];
                    }
                  }}
                  labelFormatter={(label) => formatDate(label)}
                />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="usdt_balance" 
                  stroke="#00ff88" 
                  strokeWidth={2}
                  dot={{ fill: '#00ff88', strokeWidth: 2, r: 4 }}
                  name="USDT Balance"
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="btc_balance" 
                  stroke="#ffaa00" 
                  strokeWidth={2}
                  dot={{ fill: '#ffaa00', strokeWidth: 2, r: 4 }}
                  name="BTC Balance"
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}

        {error && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Alert severity="error" sx={{ color: 'error.main' }}>{error}</Alert>
          </Box>
        )}

        {!loading && !error && chartData && chartData.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" component="h3" sx={{ color: 'white', mb: 2 }}>
              Portfolio History Data
            </Typography>
            <TableContainer component={Paper} sx={{ bgcolor: 'grey.700' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ color: 'grey.300' }}>Date</TableCell>
                    <TableCell align="right" sx={{ color: 'grey.300' }}>Portfolio Value</TableCell>
                    <TableCell align="right" sx={{ color: 'grey.300' }}>Return %</TableCell>
                    <TableCell align="right" sx={{ color: 'grey.300' }}>USDT Balance</TableCell>
                    <TableCell align="right" sx={{ color: 'grey.300' }}>BTC Balance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {chartData.map((point, index) => (
                    <TableRow key={index}>
                      <TableCell sx={{ color: 'grey.300' }}>{formatDate(point.timestamp)}</TableCell>
                      <TableCell align="right" sx={{ color: 'white' }}>{formatCurrency(point.portfolio_value)}</TableCell>
                      <TableCell align="right" sx={{ color: point.total_return_percentage >= 0 ? 'success.main' : 'error.main' }}>
                        {formatPercentage(point.total_return_percentage)}
                      </TableCell>
                      <TableCell align="right" sx={{ color: 'grey.300' }}>{formatCurrency(point.usdt_balance)}</TableCell>
                      <TableCell align="right" sx={{ color: 'grey.300' }}>{point.btc_balance.toFixed(8)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="contained" color="primary">
          Close Chart
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PortfolioChart;
