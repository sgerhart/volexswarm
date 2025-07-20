import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
} from '@mui/material';
import { AccountBalance } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { format } from 'date-fns';
import { getTrades } from '../api/system';

const Trades: React.FC = () => {
  const { data: trades, isLoading } = useQuery('trades', getTrades);

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
          Trade History
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        Trade History
      </Typography>

      {trades && trades.length > 0 ? (
        <Box>
          {trades.map((trade, index) => (
            <Card key={index} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {trade.symbol}
                  </Typography>
                  <Chip
                    label={trade.side}
                    color={trade.side === 'BUY' ? 'success' : 'error'}
                    icon={<AccountBalance />}
                  />
                </Box>
                
                <Typography variant="body2">
                  {trade.quantity} @ ${trade.price}
                </Typography>
                
                <Typography variant="body2" color="text.secondary">
                  {format(new Date(trade.timestamp), 'MMM dd, yyyy HH:mm:ss')}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      ) : (
        <Typography color="text.secondary">No trades available</Typography>
      )}
    </Box>
  );
};

export default Trades; 