import React, { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Card,
  CardContent,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  useTheme,
  useMediaQuery,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Divider,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  ShowChart as ChartIcon,
  AccountBalance as TradingIcon,
  Psychology as AiIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Refresh as RefreshIcon,
  Notifications as NotificationsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as MoneyIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import AgentStatus from './AgentStatus';
import SystemMetrics from './SystemMetrics';
import TradingOverview from './TradingOverview';
import AgentLogs from './AgentLogs';
import AgentManagement from './AgentManagement';
import TradingInterface from './TradingInterface';
import StrategyManagement from './StrategyManagement';
import SystemMonitoring from './SystemMonitoring';

interface FinancialMetrics {
  totalPortfolioValue: number;
  dailyPnL: number;
  totalPnL: number;
  winRate: number;
  totalTrades: number;
  openPositions: number;
  maxDrawdown: number;
  sharpeRatio: number;
}

interface RecentTrade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: string;
  pnl?: number;
  status: 'completed' | 'pending' | 'cancelled';
}

interface ActivePosition {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  unrealizedPnLPct: number;
}

const Dashboard: React.FC = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeComponent, setActiveComponent] = useState('dashboard');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Mock financial data (zeros for now)
  const financialMetrics: FinancialMetrics = {
    totalPortfolioValue: 0,
    dailyPnL: 0,
    totalPnL: 0,
    winRate: 0,
    totalTrades: 0,
    openPositions: 0,
    maxDrawdown: 0,
    sharpeRatio: 0,
  };

  const recentTrades: RecentTrade[] = [
    // Empty for now - will show "No recent trades" message
  ];

  const activePositions: ActivePosition[] = [
    // Empty for now - will show "No open positions" message
  ];

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, component: 'dashboard' },
    { text: 'Trading', icon: <TradingIcon />, component: 'trading' },
    { text: 'Strategy Management', icon: <AiIcon />, component: 'strategy' },
    { text: 'Infrastructure', icon: <StorageIcon />, component: 'infrastructure' },
  ];

  const renderComponent = () => {
    switch (activeComponent) {
      case 'dashboard':
        return (
          <Box>
            <Typography variant="h4" gutterBottom sx={{ color: 'primary.main', mb: 3 }}>
              VolexSwarm Dashboard
            </Typography>
            
            {/* Financial Overview */}
            <FinancialOverview metrics={financialMetrics} trades={recentTrades} positions={activePositions} />
            
            <Box sx={{ mt: 4 }}>
              <TradingOverview />
            </Box>
            
            <Box sx={{ mt: 4 }}>
              <AgentLogs />
            </Box>
          </Box>
        );
      case 'trading':
        return <TradingInterface />;
      case 'strategy':
        return <StrategyManagement />;
      case 'infrastructure':
        return (
          <Box>
            <Typography variant="h4" gutterBottom sx={{ color: 'primary.main', mb: 3 }}>
              Infrastructure & System Monitoring
            </Typography>
            
            <AgentStatus />
            
            <Box sx={{ mt: 4 }}>
              <SystemMetrics />
            </Box>
            
            <Box sx={{ mt: 4 }}>
              <SystemMonitoring />
            </Box>
          </Box>
        );
      default:
        return null;
    }
  };

  const drawer = (
    <Box sx={{ width: 250 }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 'bold' }}>
          VolexSwarm
        </Typography>
        <Typography variant="caption" color="text.secondary">
          AI Trading Platform
        </Typography>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem
            key={item.text}
            onClick={() => {
              setActiveComponent(item.component);
              if (isMobile) setDrawerOpen(false);
            }}
            sx={{
              cursor: 'pointer',
              backgroundColor: activeComponent === item.component ? 'primary.main' : 'transparent',
              color: activeComponent === item.component ? 'primary.contrastText' : 'inherit',
              '&:hover': {
                backgroundColor: activeComponent === item.component ? 'primary.dark' : 'action.hover',
              },
            }}
          >
            <ListItemIcon sx={{ color: 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            VolexSwarm - AI Trading System
          </Typography>
          <IconButton color="inherit">
            <RefreshIcon />
          </IconButton>
          <IconButton color="inherit">
            <NotificationsIcon />
          </IconButton>
          <Chip
            label="System Online"
            color="success"
            size="small"
            sx={{ ml: 2 }}
          />
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: 250 }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={drawerOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { width: 250, backgroundColor: 'background.paper' },
          }}
        >
          {drawer}
        </Drawer>
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { width: 250, backgroundColor: 'background.paper' },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - 250px)` },
          mt: 8,
        }}
      >
        <Container maxWidth="xl">
          {renderComponent()}
        </Container>
      </Box>
    </Box>
  );
};

// Financial Overview Component
const FinancialOverview: React.FC<{
  metrics: FinancialMetrics;
  trades: RecentTrade[];
  positions: ActivePosition[];
}> = ({ metrics, trades, positions }) => {
  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', mb: 3 }}>
        Financial Overview
      </Typography>

      {/* Key Metrics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="textSecondary" gutterBottom>
                  Portfolio Value
                </Typography>
                <Typography variant="h5" component="div">
                  ${metrics.totalPortfolioValue.toLocaleString()}
                </Typography>
              </Box>
              <MoneyIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="textSecondary" gutterBottom>
                  Daily P&L
                </Typography>
                <Typography 
                  variant="h5" 
                  component="div"
                  color={metrics.dailyPnL >= 0 ? 'success.main' : 'error.main'}
                >
                  ${metrics.dailyPnL.toLocaleString()}
                </Typography>
              </Box>
              {metrics.dailyPnL >= 0 ? (
                <TrendingUpIcon sx={{ fontSize: 40, color: 'success.main' }} />
              ) : (
                <TrendingDownIcon sx={{ fontSize: 40, color: 'error.main' }} />
              )}
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="textSecondary" gutterBottom>
                  Total P&L
                </Typography>
                <Typography 
                  variant="h5" 
                  component="div"
                  color={metrics.totalPnL >= 0 ? 'success.main' : 'error.main'}
                >
                  ${metrics.totalPnL.toLocaleString()}
                </Typography>
              </Box>
              <ChartIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography color="textSecondary" gutterBottom>
                  Win Rate
                </Typography>
                <Typography variant="h5" component="div">
                  {metrics.winRate.toFixed(1)}%
                </Typography>
              </Box>
              <CheckCircleIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Performance Metrics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 3, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance Metrics
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Total Trades</Typography>
                <Typography fontWeight="bold">{metrics.totalTrades}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Open Positions</Typography>
                <Typography fontWeight="bold">{metrics.openPositions}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Max Drawdown</Typography>
                <Typography fontWeight="bold" color="error.main">
                  {metrics.maxDrawdown.toFixed(2)}%
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Sharpe Ratio</Typography>
                <Typography fontWeight="bold">{metrics.sharpeRatio.toFixed(2)}</Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Active Positions
            </Typography>
            {positions.length > 0 ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Side</TableCell>
                      <TableCell>Quantity</TableCell>
                      <TableCell>Unrealized P&L</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {positions.map((position) => (
                      <TableRow key={position.symbol}>
                        <TableCell>{position.symbol}</TableCell>
                        <TableCell>
                          <Chip 
                            label={position.side} 
                            size="small"
                            color={position.side === 'long' ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell>{position.quantity}</TableCell>
                        <TableCell color={position.unrealizedPnL >= 0 ? 'success.main' : 'error.main'}>
                          ${position.unrealizedPnL.toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography color="textSecondary" sx={{ textAlign: 'center', py: 4 }}>
                No open positions
              </Typography>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Recent Trades */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Trades
          </Typography>
          {trades.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Time</TableCell>
                    <TableCell>Symbol</TableCell>
                    <TableCell>Side</TableCell>
                    <TableCell>Quantity</TableCell>
                    <TableCell>Price</TableCell>
                    <TableCell>P&L</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trades.map((trade) => (
                    <TableRow key={trade.id}>
                      <TableCell>{new Date(trade.timestamp).toLocaleString()}</TableCell>
                      <TableCell>{trade.symbol}</TableCell>
                      <TableCell>
                        <Chip 
                          label={trade.side} 
                          size="small"
                          color={trade.side === 'buy' ? 'success' : 'error'}
                        />
                      </TableCell>
                      <TableCell>{trade.quantity}</TableCell>
                      <TableCell>${trade.price.toFixed(2)}</TableCell>
                      <TableCell color={trade.pnl && trade.pnl >= 0 ? 'success.main' : 'error.main'}>
                        {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={trade.status} 
                          size="small"
                          color={trade.status === 'completed' ? 'success' : 'warning'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography color="textSecondary" sx={{ textAlign: 'center', py: 4 }}>
              No recent trades
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard; 