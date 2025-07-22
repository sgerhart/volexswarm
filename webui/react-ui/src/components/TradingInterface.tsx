import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import {
  TrendingUp as ProfitIcon,
  TrendingDown as LossIcon,
  AccountBalance as BalanceIcon,
  ShowChart as ChartIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: string;
  status: 'open' | 'filled' | 'cancelled' | 'rejected';
  pnl?: number;
  strategy?: string;
}

interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  realizedPnl: number;
  timestamp: string;
}

interface Balance {
  currency: string;
  available: number;
  total: number;
  inUse: number;
}

const TradingInterface: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [newOrderDialog, setNewOrderDialog] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [orderQuantity, setOrderQuantity] = useState('');
  const [orderPrice, setOrderPrice] = useState('');
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy');

  // Mock data
  useEffect(() => {
    // Simulate fetching trading data
    const mockTrades: Trade[] = [
      {
        id: '1',
        symbol: 'BTC/USD',
        side: 'buy',
        quantity: 0.1,
        price: 45000,
        timestamp: new Date().toISOString(),
        status: 'filled',
        pnl: 250,
        strategy: 'Moving Average Crossover',
      },
      {
        id: '2',
        symbol: 'ETH/USD',
        side: 'sell',
        quantity: 1.5,
        price: 3200,
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        status: 'open',
        strategy: 'RSI Strategy',
      },
    ];

    const mockPositions: Position[] = [
      {
        symbol: 'BTC/USD',
        quantity: 0.1,
        avgPrice: 45000,
        currentPrice: 45250,
        unrealizedPnl: 25,
        realizedPnl: 0,
        timestamp: new Date().toISOString(),
      },
      {
        symbol: 'ETH/USD',
        quantity: -1.5,
        avgPrice: 3200,
        currentPrice: 3180,
        unrealizedPnl: 30,
        realizedPnl: 0,
        timestamp: new Date().toISOString(),
      },
    ];

    const mockBalances: Balance[] = [
      {
        currency: 'USD',
        available: 15000,
        total: 15000,
        inUse: 0,
      },
      {
        currency: 'BTC',
        available: 0.1,
        total: 0.1,
        inUse: 0,
      },
      {
        currency: 'ETH',
        available: 2.5,
        total: 2.5,
        inUse: 0,
      },
    ];

    setTrades(mockTrades);
    setPositions(mockPositions);
    setBalances(mockBalances);
  }, []);

  const handleNewOrder = () => {
    if (!selectedSymbol || !orderQuantity || !orderPrice) {
      return;
    }

    const newTrade: Trade = {
      id: Date.now().toString(),
      symbol: selectedSymbol,
      side: orderSide,
      quantity: parseFloat(orderQuantity),
      price: parseFloat(orderPrice),
      timestamp: new Date().toISOString(),
      status: 'open',
    };

    setTrades(prev => [newTrade, ...prev]);
    setNewOrderDialog(false);
    setSelectedSymbol('');
    setOrderQuantity('');
    setOrderPrice('');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'filled':
        return 'success';
      case 'open':
        return 'warning';
      case 'cancelled':
        return 'error';
      case 'rejected':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPnlColor = (pnl: number) => {
    return pnl >= 0 ? 'success' : 'error';
  };

  const getPnlIcon = (pnl: number) => {
    return pnl >= 0 ? <ProfitIcon /> : <LossIcon />;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ color: 'primary.main' }}>
          Trading Interface
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setNewOrderDialog(true)}
        >
          New Order
        </Button>
      </Box>

      {/* Account Overview */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BalanceIcon color="primary" />
              <Typography color="textSecondary" gutterBottom>
                Total Balance
              </Typography>
            </Box>
            <Typography variant="h4" sx={{ color: 'primary.main' }}>
              ${balances.reduce((sum, b) => sum + b.total, 0).toLocaleString()}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ProfitIcon color="success" />
              <Typography color="textSecondary" gutterBottom>
                Total P&L
              </Typography>
            </Box>
            <Typography variant="h4" sx={{ color: 'success.main' }}>
              ${positions.reduce((sum, p) => sum + p.unrealizedPnl + p.realizedPnl, 0).toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Open Positions
            </Typography>
            <Typography variant="h4" sx={{ color: 'warning.main' }}>
              {positions.length}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Active Orders
            </Typography>
            <Typography variant="h4" sx={{ color: 'info.main' }}>
              {trades.filter(t => t.status === 'open').length}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Trading Tabs */}
      <Card>
        <CardContent>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="Positions" />
            <Tab label="Orders" />
            <Tab label="Balances" />
            <Tab label="History" />
          </Tabs>

          <Divider sx={{ my: 2 }} />

          {/* Positions Tab */}
          {activeTab === 0 && (
            <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Quantity</TableCell>
                    <TableCell>Avg Price</TableCell>
                    <TableCell>Current Price</TableCell>
                    <TableCell>Unrealized P&L</TableCell>
                    <TableCell>Realized P&L</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {positions.map((position) => (
                    <TableRow key={position.symbol} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {position.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={position.quantity > 0 ? 'LONG' : 'SHORT'}
                          color={position.quantity > 0 ? 'success' : 'error'}
                          size="small"
                        />
                        <Typography variant="body2">
                          {Math.abs(position.quantity)}
                        </Typography>
                      </TableCell>
                      <TableCell>${position.avgPrice.toLocaleString()}</TableCell>
                      <TableCell>${position.currentPrice.toLocaleString()}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getPnlIcon(position.unrealizedPnl)}
                          <Typography
                            variant="body2"
                            sx={{ color: getPnlColor(position.unrealizedPnl) + '.main' }}
                          >
                            ${position.unrealizedPnl.toFixed(2)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ color: getPnlColor(position.realizedPnl) + '.main' }}
                        >
                          ${position.realizedPnl.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Button size="small" variant="outlined" color="error">
                          Close
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Orders Tab */}
          {activeTab === 1 && (
            <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell>Quantity</TableCell>
                    <TableCell>Price</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>P&L</TableCell>
                    <TableCell>Strategy</TableCell>
                    <TableCell>Time</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trades.map((trade) => (
                    <TableRow key={trade.id} hover>
                      <TableCell>{trade.symbol}</TableCell>
                      <TableCell>
                        <Chip
                          label={trade.side.toUpperCase()}
                          color={trade.side === 'buy' ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{trade.quantity}</TableCell>
                      <TableCell>${trade.price.toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip
                          label={trade.status}
                          color={getStatusColor(trade.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {trade.pnl && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getPnlIcon(trade.pnl)}
                            <Typography
                              variant="body2"
                              sx={{ color: getPnlColor(trade.pnl) + '.main' }}
                            >
                              ${trade.pnl.toFixed(2)}
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell>{trade.strategy || '-'}</TableCell>
                      <TableCell>
                        {new Date(trade.timestamp).toLocaleTimeString()}
                      </TableCell>
                      <TableCell>
                        {trade.status === 'open' && (
                          <Button size="small" variant="outlined" color="error">
                            Cancel
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Balances Tab */}
          {activeTab === 2 && (
            <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Currency</TableCell>
                    <TableCell>Available</TableCell>
                    <TableCell>In Use</TableCell>
                    <TableCell>Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {balances.map((balance) => (
                    <TableRow key={balance.currency} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {balance.currency}
                        </Typography>
                      </TableCell>
                      <TableCell>{balance.available.toLocaleString()}</TableCell>
                      <TableCell>{balance.inUse.toLocaleString()}</TableCell>
                      <TableCell>{balance.total.toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* History Tab */}
          {activeTab === 3 && (
            <Box>
              <Typography variant="body1" color="textSecondary">
                Trading history and analytics coming soon...
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* New Order Dialog */}
      <Dialog open={newOrderDialog} onClose={() => setNewOrderDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Order</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Symbol</InputLabel>
              <Select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                label="Symbol"
              >
                <MenuItem value="BTC/USD">BTC/USD</MenuItem>
                <MenuItem value="ETH/USD">ETH/USD</MenuItem>
                <MenuItem value="ADA/USD">ADA/USD</MenuItem>
                <MenuItem value="SOL/USD">SOL/USD</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Side</InputLabel>
              <Select
                value={orderSide}
                onChange={(e) => setOrderSide(e.target.value as 'buy' | 'sell')}
                label="Side"
              >
                <MenuItem value="buy">Buy</MenuItem>
                <MenuItem value="sell">Sell</MenuItem>
              </Select>
            </FormControl>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={orderQuantity}
                onChange={(e) => setOrderQuantity(e.target.value)}
              />
              <TextField
                fullWidth
                label="Price"
                type="number"
                value={orderPrice}
                onChange={(e) => setOrderPrice(e.target.value)}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewOrderDialog(false)}>Cancel</Button>
          <Button onClick={handleNewOrder} variant="contained">
            Place Order
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TradingInterface; 