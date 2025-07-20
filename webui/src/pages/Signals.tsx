import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
} from '@mui/material';
import { TrendingUp } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { format } from 'date-fns';
import { getSignals } from '../api/system';

const Signals: React.FC = () => {
  const { data: signals, isLoading } = useQuery('signals', getSignals);

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
          Trading Signals
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        Trading Signals
      </Typography>

      {signals && signals.length > 0 ? (
        <Box>
          {signals.map((signal, index) => (
            <Card key={index} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {signal.symbol}
                  </Typography>
                  <Chip
                    label={signal.signal_type}
                    color={signal.signal_type === 'BUY' ? 'success' : 'error'}
                    icon={<TrendingUp />}
                  />
                </Box>
                
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <Chip label={`Confidence: ${signal.confidence.toFixed(1)}%`} variant="outlined" />
                  <Chip label={`Strength: ${signal.strength.toFixed(1)}`} variant="outlined" />
                </Box>
                
                <Typography variant="body2" color="text.secondary">
                  {format(new Date(signal.timestamp), 'MMM dd, yyyy HH:mm:ss')}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      ) : (
        <Typography color="text.secondary">No signals available</Typography>
      )}
    </Box>
  );
};

export default Signals; 