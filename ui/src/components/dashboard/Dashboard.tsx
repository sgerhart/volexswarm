import React, { useState } from 'react';
import { Box, Card, CardContent, Typography, Button, Chip, Alert, CircularProgress } from '@mui/material';
import { TrendingUp, TrendingDown, AccountBalance, ShowChart, Refresh as RefreshIcon } from '@mui/icons-material';
import PortfolioChart from './PortfolioChart';
import SimulationModeControl from './SimulationModeControl';
import { useAppStore } from '../../store';
import { PortfolioData } from '../../types';
import { useDataFetching } from '../../hooks/useDataFetching';

const Dashboard: React.FC = () => {
  const { portfolio, tradingSignals, activeStrategies } = useAppStore();
  const { isLoading, error, refreshData } = useDataFetching();
  const [isChartOpen, setIsChartOpen] = useState(false);
  const [isSimulationControlOpen, setIsSimulationControlOpen] = useState(false);
  
  // Get portfolio data from store with fallback
  const currentPortfolio: PortfolioData = portfolio || {
    totalValue: 0,
    unrealizedPnL: 0,
    realizedPnL: 0,
    positions: [],
    performance: {
      totalReturn: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      winRate: 0,
      profitFactor: 0,
      totalTrades: 0,
      winningTrades: 0,
      losingTrades: 0,
      averageWin: 0,
      averageLoss: 0
    },
    timestamp: new Date().toISOString()
  };

  // Debug logging to see what's in the store
  console.log('🔍 Dashboard: portfolio from store:', portfolio);
  console.log('🔍 Dashboard: currentPortfolio fallback:', currentPortfolio);

  const handlePortfolioClick = () => {
    console.log('🔍 Portfolio Value card clicked!');
    console.log('🔍 Current isChartOpen state:', isChartOpen);
    setIsChartOpen(true);
    console.log('🔍 Set isChartOpen to true');
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with Simulation Mode Control */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" sx={{ color: 'text.primary' }}>
          Trading Dashboard
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={isLoading ? <CircularProgress size={20} /> : <RefreshIcon />}
            onClick={refreshData}
            disabled={isLoading}
            sx={{ 
              borderColor: 'primary.main',
              color: 'primary.main',
              '&:hover': {
                borderColor: 'primary.dark',
                backgroundColor: 'primary.main',
                color: 'white'
              }
            }}
          >
            {isLoading ? 'Refreshing...' : 'Refresh Data'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<ShowChart />}
            onClick={() => setIsSimulationControlOpen(true)}
            sx={{ 
              borderColor: 'primary.main',
              color: 'primary.main',
              '&:hover': {
                borderColor: 'primary.dark',
                backgroundColor: 'primary.main',
                color: 'white'
              }
            }}
          >
            Simulation Mode Control
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {/* Simulation Mode Status Alert */}
      <Alert 
        severity="info" 
        sx={{ mb: 3 }}
        action={
          <Button 
            color="inherit" 
            size="small"
            onClick={() => setIsSimulationControlOpen(true)}
          >
            Configure
          </Button>
        }
      >
        🔬 Currently in Simulation Mode - All trades are simulated for safe testing
      </Alert>

      {/* Debug Portfolio Data */}
      {portfolio && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <strong>✅ Portfolio Data Loaded:</strong> ${portfolio.totalValue?.toFixed(2)} | 
          Positions: {portfolio.positions?.length || 0} | 
          BTC: {portfolio.positions?.find(p => p.symbol === 'BTC')?.quantity?.toFixed(8) || '0'} | 
          USDT: ${portfolio.positions?.find(p => p.symbol === 'USDT')?.quantity?.toFixed(2) || '0'}
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && !portfolio && (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress size={60} />
        </Box>
      )}
      
      {/* Portfolio Metrics Grid */}
      {!isLoading && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 3 }}>
        {/* Portfolio Value Card */}
        <Box>
          <Card 
            sx={{ 
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 8,
                borderColor: 'primary.main'
              }
            }}
            onClick={handlePortfolioClick}
          >
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Portfolio Value
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ color: 'text.primary' }}>
                    ${currentPortfolio.totalValue?.toLocaleString() || '0'}
                  </Typography>
                </Box>
                <AccountBalance sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Click to view chart
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Total Return Card */}
        <Box>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Return
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ 
                    color: currentPortfolio.performance.totalReturn >= 0 ? 'success.main' : 'error.main' 
                  }}>
                    {currentPortfolio.performance.totalReturn >= 0 ? '+' : ''}{currentPortfolio.performance.totalReturn?.toFixed(2) || '0'}%
                  </Typography>
                </Box>
                {currentPortfolio.performance.totalReturn >= 0 ? (
                  <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />
                ) : (
                  <TrendingDown sx={{ fontSize: 40, color: 'error.main' }} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* P&L Card */}
        <Box>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    P&L
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ 
                    color: currentPortfolio.unrealizedPnL >= 0 ? 'success.main' : 'error.main' 
                  }}>
                    ${currentPortfolio.unrealizedPnL?.toLocaleString() || '0'}
                  </Typography>
                </Box>
                {currentPortfolio.unrealizedPnL >= 0 ? (
                  <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />
                ) : (
                  <TrendingDown sx={{ fontSize: 40, color: 'error.main' }} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Active Strategies Card */}
        <Box>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Active Strategies
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ color: 'text.primary' }}>
                    {activeStrategies?.length || 0}
                  </Typography>
                </Box>
                <ShowChart sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* BTC Balance Card */}
        <Box>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    BTC Balance
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ color: 'text.primary' }}>
                    {currentPortfolio.positions?.find(p => p.symbol === 'BTC')?.quantity?.toFixed(8) || '0.00000000'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    ${currentPortfolio.positions?.find(p => p.symbol === 'BTC')?.totalValue?.toFixed(2) || '0.00'}
                  </Typography>
                </Box>
                <Typography variant="h6" sx={{ color: 'warning.main', fontWeight: 'bold' }}>
                  ₿
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* USDT Balance Card */}
        <Box>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    USDT Balance
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ color: 'text.primary' }}>
                    ${currentPortfolio.positions?.find(p => p.symbol === 'USDT')?.quantity?.toFixed(2) || '0.00'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Available for trading
                  </Typography>
                </Box>
                <Typography variant="h6" sx={{ color: 'success.main', fontWeight: 'bold' }}>
                  💰
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>
      )}
      
      {/* Trading Signals Section */}
      {tradingSignals && tradingSignals.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Trading Signals
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {tradingSignals.slice(0, 5).map((signal: any, index: number) => (
                <Chip
                  key={index}
                  label={`${signal.symbol}: ${signal.signal}`}
                  color={signal.signal === 'BUY' ? 'success' : 'error'}
                  variant="outlined"
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Portfolio Chart Modal */}
      <PortfolioChart 
        isOpen={isChartOpen} 
        onClose={() => setIsChartOpen(false)} 
        currentPortfolio={currentPortfolio}
      />

      {/* Simulation Mode Control Modal */}
      <SimulationModeControl
        open={isSimulationControlOpen}
        onClose={() => setIsSimulationControlOpen(false)}
      />
    </Box>
  );
};

export default Dashboard;
