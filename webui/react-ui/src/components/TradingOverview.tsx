import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  TrendingUp as ProfitIcon,
  TrendingDown as LossIcon,
  AccountBalance as PortfolioIcon,
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingUp,
} from '@mui/icons-material';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TradingData {
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: string;
  status: 'completed' | 'pending' | 'cancelled';
}

const TradingOverview: React.FC = () => {
  const [portfolioValue, setPortfolioValue] = useState(125000);
  const [dailyPnL, setDailyPnL] = useState(2340);
  const [totalPnL, setTotalPnL] = useState(15680);
  const [activePositions, setActivePositions] = useState(8);
  const [recentTrades, setRecentTrades] = useState<TradingData[]>([
    { symbol: 'BTC/USDT', side: 'buy', quantity: 0.5, price: 43250, timestamp: '2024-01-15T10:30:00Z', status: 'completed' },
    { symbol: 'ETH/USDT', side: 'sell', quantity: 2.1, price: 2650, timestamp: '2024-01-15T10:25:00Z', status: 'completed' },
    { symbol: 'ADA/USDT', side: 'buy', quantity: 1000, price: 0.48, timestamp: '2024-01-15T10:20:00Z', status: 'pending' },
    { symbol: 'SOL/USDT', side: 'sell', quantity: 15, price: 98.5, timestamp: '2024-01-15T10:15:00Z', status: 'completed' },
  ]);

  const [chartData, setChartData] = useState([
    { time: '09:00', value: 122000 },
    { time: '10:00', value: 123500 },
    { time: '11:00', value: 124200 },
    { time: '12:00', value: 125000 },
    { time: '13:00', value: 125800 },
    { time: '14:00', value: 126200 },
    { time: '15:00', value: 125000 },
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate real-time portfolio updates
      setPortfolioValue(prev => prev + (Math.random() - 0.5) * 1000);
      setDailyPnL(prev => prev + (Math.random() - 0.5) * 100);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getPnLColor = (value: number) => {
    return value >= 0 ? 'success' : 'error';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', mb: 3 }}>
          Trading Overview
        </Typography>

        {/* Portfolio Summary */}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
          <Box sx={{ textAlign: 'center', minWidth: 150, flex: 1 }}>
            <PortfolioIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              {formatCurrency(portfolioValue)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Portfolio Value
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: 150, flex: 1 }}>
            <MoneyIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'success.main' }}>
              {formatCurrency(dailyPnL)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Daily P&L
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: 150, flex: 1 }}>
            <ProfitIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'success.main' }}>
              {formatCurrency(totalPnL)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total P&L
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center', minWidth: 150, flex: 1 }}>
            <TrendingUp sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              {activePositions}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Active Positions
            </Typography>
          </Box>
        </Box>

        {/* Portfolio Chart */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Portfolio Performance
          </Typography>
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="time" stroke="#b0b0b0" />
              <YAxis stroke="#b0b0b0" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #333',
                  borderRadius: 8,
                }}
                formatter={(value: any) => [formatCurrency(value), 'Portfolio Value']}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#00d4aa"
                fill="#00d4aa"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Box>

        {/* Recent Trades */}
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Recent Trades
            </Typography>
            <Button variant="outlined" size="small">
              View All
            </Button>
          </Box>
          <TableContainer component={Paper} sx={{ backgroundColor: 'transparent' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: 'text.secondary' }}>Symbol</TableCell>
                  <TableCell sx={{ color: 'text.secondary' }}>Side</TableCell>
                  <TableCell sx={{ color: 'text.secondary' }}>Quantity</TableCell>
                  <TableCell sx={{ color: 'text.secondary' }}>Price</TableCell>
                  <TableCell sx={{ color: 'text.secondary' }}>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentTrades.map((trade, index) => (
                  <TableRow key={index}>
                    <TableCell sx={{ color: 'text.primary' }}>{trade.symbol}</TableCell>
                    <TableCell>
                      <Chip
                        label={trade.side.toUpperCase()}
                        color={trade.side === 'buy' ? 'success' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell sx={{ color: 'text.primary' }}>{trade.quantity}</TableCell>
                    <TableCell sx={{ color: 'text.primary' }}>${trade.price.toLocaleString()}</TableCell>
                    <TableCell>
                      <Chip
                        label={trade.status}
                        color={getStatusColor(trade.status) as any}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TradingOverview; 