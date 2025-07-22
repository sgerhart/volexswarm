import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Divider,
  Switch,
  FormControlLabel,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  TrendingUp as PerformanceIcon,
  Psychology as AiIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface Strategy {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'testing';
  performance: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
  };
  parameters: Record<string, any>;
  createdAt: string;
  lastUpdated: string;
}

const StrategyManagement: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [newStrategyDialog, setNewStrategyDialog] = useState(false);
  const [editStrategyDialog, setEditStrategyDialog] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [strategyName, setStrategyName] = useState('');
  const [strategyType, setStrategyType] = useState('');
  const [strategyParameters, setStrategyParameters] = useState<Record<string, any>>({});

  // Mock data
  useEffect(() => {
    const mockStrategies: Strategy[] = [
      {
        id: '1',
        name: 'Moving Average Crossover',
        type: 'moving_average',
        status: 'active',
        performance: {
          totalReturn: 15.7,
          sharpeRatio: 1.2,
          maxDrawdown: -8.3,
          winRate: 62.5,
        },
        parameters: {
          shortPeriod: 10,
          longPeriod: 30,
          threshold: 0.02,
        },
        createdAt: '2024-01-15T10:30:00Z',
        lastUpdated: '2024-01-20T14:45:00Z',
      },
      {
        id: '2',
        name: 'RSI Strategy',
        type: 'rsi',
        status: 'active',
        performance: {
          totalReturn: 12.3,
          sharpeRatio: 0.9,
          maxDrawdown: -12.1,
          winRate: 58.2,
        },
        parameters: {
          period: 14,
          overbought: 70,
          oversold: 30,
        },
        createdAt: '2024-01-10T09:15:00Z',
        lastUpdated: '2024-01-19T16:20:00Z',
      },
      {
        id: '3',
        name: 'Composite Strategy',
        type: 'composite',
        status: 'testing',
        performance: {
          totalReturn: 18.9,
          sharpeRatio: 1.4,
          maxDrawdown: -6.8,
          winRate: 65.1,
        },
        parameters: {
          strategies: ['moving_average', 'rsi'],
          weights: [0.6, 0.4],
          combination: 'weighted',
        },
        createdAt: '2024-01-18T11:00:00Z',
        lastUpdated: '2024-01-20T10:30:00Z',
      },
    ];

    setStrategies(mockStrategies);
  }, []);

  const handleCreateStrategy = () => {
    if (!strategyName || !strategyType) {
      return;
    }

    const newStrategy: Strategy = {
      id: Date.now().toString(),
      name: strategyName,
      type: strategyType,
      status: 'inactive',
      performance: {
        totalReturn: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        winRate: 0,
      },
      parameters: strategyParameters,
      createdAt: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
    };

    setStrategies(prev => [newStrategy, ...prev]);
    setNewStrategyDialog(false);
    setStrategyName('');
    setStrategyType('');
    setStrategyParameters({});
  };

  const handleEditStrategy = () => {
    if (!selectedStrategy || !strategyName) {
      return;
    }

    setStrategies(prev => prev.map(strategy =>
      strategy.id === selectedStrategy.id
        ? {
            ...strategy,
            name: strategyName,
            parameters: strategyParameters,
            lastUpdated: new Date().toISOString(),
          }
        : strategy
    ));

    setEditStrategyDialog(false);
    setSelectedStrategy(null);
    setStrategyName('');
    setStrategyParameters({});
  };

  const handleToggleStrategy = (strategyId: string) => {
    setStrategies(prev => prev.map(strategy =>
      strategy.id === strategyId
        ? {
            ...strategy,
            status: strategy.status === 'active' ? 'inactive' : 'active',
            lastUpdated: new Date().toISOString(),
          }
        : strategy
    ));
  };

  const handleDeleteStrategy = (strategyId: string) => {
    setStrategies(prev => prev.filter(strategy => strategy.id !== strategyId));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'testing':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getPerformanceColor = (value: number, type: 'return' | 'sharpe' | 'drawdown' | 'winrate') => {
    if (type === 'drawdown') {
      return value <= -10 ? 'error' : value <= -5 ? 'warning' : 'success';
    }
    if (type === 'winrate') {
      return value >= 60 ? 'success' : value >= 50 ? 'warning' : 'error';
    }
    return value > 0 ? 'success' : 'error';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ color: 'primary.main' }}>
          Strategy Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setNewStrategyDialog(true)}
        >
          New Strategy
        </Button>
      </Box>

      {/* Strategy Overview */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Strategies
            </Typography>
            <Typography variant="h4" sx={{ color: 'primary.main' }}>
              {strategies.length}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Active Strategies
            </Typography>
            <Typography variant="h4" sx={{ color: 'success.main' }}>
              {strategies.filter(s => s.status === 'active').length}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Avg Performance
            </Typography>
            <Typography variant="h4" sx={{ color: 'info.main' }}>
              {strategies.length > 0 
                ? (strategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) / strategies.length).toFixed(1)
                : '0'
              }%
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Strategy Tabs */}
      <Card>
        <CardContent>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="All Strategies" />
            <Tab label="Active" />
            <Tab label="Testing" />
            <Tab label="Templates" />
          </Tabs>

          <Divider sx={{ my: 2 }} />

          {/* Strategies Table */}
          <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Strategy</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Total Return</TableCell>
                  <TableCell>Sharpe Ratio</TableCell>
                  <TableCell>Max Drawdown</TableCell>
                  <TableCell>Win Rate</TableCell>
                  <TableCell>Last Updated</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {strategies
                  .filter(strategy => {
                    if (activeTab === 1) return strategy.status === 'active';
                    if (activeTab === 2) return strategy.status === 'testing';
                    return true;
                  })
                  .map((strategy) => (
                    <TableRow key={strategy.id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {strategy.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={strategy.type} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={strategy.status}
                          color={getStatusColor(strategy.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ color: getPerformanceColor(strategy.performance.totalReturn, 'return') + '.main' }}
                        >
                          {strategy.performance.totalReturn.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ color: getPerformanceColor(strategy.performance.sharpeRatio, 'sharpe') + '.main' }}
                        >
                          {strategy.performance.sharpeRatio.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ color: getPerformanceColor(strategy.performance.maxDrawdown, 'drawdown') + '.main' }}
                        >
                          {strategy.performance.maxDrawdown.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ color: getPerformanceColor(strategy.performance.winRate, 'winrate') + '.main' }}
                        >
                          {strategy.performance.winRate.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {new Date(strategy.lastUpdated).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => {
                              setSelectedStrategy(strategy);
                              setStrategyName(strategy.name);
                              setStrategyParameters(strategy.parameters);
                              setEditStrategyDialog(true);
                            }}
                          >
                            <EditIcon fontSize="small" />
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color={strategy.status === 'active' ? 'error' : 'success'}
                            onClick={() => handleToggleStrategy(strategy.id)}
                          >
                            {strategy.status === 'active' ? <StopIcon fontSize="small" /> : <StartIcon fontSize="small" />}
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            onClick={() => handleDeleteStrategy(strategy.id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* New Strategy Dialog */}
      <Dialog open={newStrategyDialog} onClose={() => setNewStrategyDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Strategy</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              label="Strategy Name"
              value={strategyName}
              onChange={(e) => setStrategyName(e.target.value)}
            />
            <FormControl fullWidth>
              <InputLabel>Strategy Type</InputLabel>
              <Select
                value={strategyType}
                onChange={(e) => setStrategyType(e.target.value)}
                label="Strategy Type"
              >
                <MenuItem value="moving_average">Moving Average Crossover</MenuItem>
                <MenuItem value="rsi">RSI Strategy</MenuItem>
                <MenuItem value="bollinger_bands">Bollinger Bands</MenuItem>
                <MenuItem value="mean_reversion">Mean Reversion</MenuItem>
                <MenuItem value="momentum">Momentum Strategy</MenuItem>
                <MenuItem value="composite">Composite Strategy</MenuItem>
              </Select>
            </FormControl>
            <Alert severity="info">
              Strategy parameters will be configured after creation.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewStrategyDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateStrategy} variant="contained">
            Create Strategy
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Strategy Dialog */}
      <Dialog open={editStrategyDialog} onClose={() => setEditStrategyDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Strategy</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              label="Strategy Name"
              value={strategyName}
              onChange={(e) => setStrategyName(e.target.value)}
            />
            <Typography variant="body2" color="textSecondary">
              Strategy Type: {selectedStrategy?.type}
            </Typography>
            <Alert severity="info">
              Advanced parameter configuration coming soon...
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditStrategyDialog(false)}>Cancel</Button>
          <Button onClick={handleEditStrategy} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrategyManagement; 