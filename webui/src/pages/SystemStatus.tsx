import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Grid,
} from '@mui/material';
import { Monitor, CheckCircle, Error, Warning } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { getSystemStatus } from '../api/system';

const SystemStatus: React.FC = () => {
  const { data: systemStatus, isLoading } = useQuery('systemStatus', getSystemStatus);

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
          System Status
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'success';
      case 'degraded':
        return 'warning';
      default:
        return 'error';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircle />;
      case 'degraded':
        return <Warning />;
      default:
        return <Error />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        System Status
      </Typography>

      {systemStatus && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Monitor />
                  <Typography variant="h6">Overall System Status</Typography>
                  <Chip
                    icon={getStatusIcon(systemStatus.status)}
                    label={systemStatus.status}
                    color={getStatusColor(systemStatus.status)}
                    variant="outlined"
                  />
                </Box>
                
                {systemStatus.metrics && (
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Total Agents
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                          {systemStatus.metrics.total_agents}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Healthy Agents
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                          {systemStatus.metrics.healthy_agents}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Active Signals
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                          {systemStatus.metrics.active_signals}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Total Trades
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                          {systemStatus.metrics.total_trades}
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default SystemStatus; 