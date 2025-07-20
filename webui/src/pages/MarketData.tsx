import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
} from '@mui/material';
import { ShowChart, TrendingUp, TrendingDown } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { getMarketData } from '../api/system';

const MarketData: React.FC = () => {
  const { data: marketData, isLoading } = useQuery('marketData', getMarketData);

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
          Market Data
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        Market Data
      </Typography>

      {marketData && Object.keys(marketData).length > 0 ? (
        <Box>
          {Object.entries(marketData).map(([symbol, data]) => (
            <Card key={symbol} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {symbol}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {data.change_24h >= 0 ? <TrendingUp color="success" /> : <TrendingDown color="error" />}
                    <Chip
                      label={`${data.change_24h >= 0 ? '+' : ''}${data.change_24h.toFixed(2)}%`}
                      color={data.change_24h >= 0 ? 'success' : 'error'}
                      variant="outlined"
                    />
                  </Box>
                </Box>
                
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                  ${data.price.toFixed(2)}
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Chip label={`High: $${data.high_24h.toFixed(2)}`} variant="outlined" size="small" />
                  <Chip label={`Low: $${data.low_24h.toFixed(2)}`} variant="outlined" size="small" />
                  <Chip label={`Vol: ${new Intl.NumberFormat().format(data.volume_24h)}`} variant="outlined" size="small" />
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      ) : (
        <Typography color="text.secondary">No market data available</Typography>
      )}
    </Box>
  );
};

export default MarketData; 