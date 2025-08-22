import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

import { ShowChart as ShowChartIcon } from '@mui/icons-material';

const Trading: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Trading Intelligence
      </Typography>
      
      <Box sx={{ display: 'grid', gap: 3 }}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <ShowChartIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Live Trading Signals</Typography>
            </Box>
            <Typography variant="body1" color="text.secondary">
              Real-time trading signals and strategy performance will be displayed here.
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default Trading;
