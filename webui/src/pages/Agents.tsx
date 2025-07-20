import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ExpandMore,
  CheckCircle,
  Error,
  Warning,
  Psychology,
  TrendingUp,
  AccountBalance,
  Monitor,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { getAgents } from '../api/system';

const Agents: React.FC = () => {
  const { data: agents, isLoading } = useQuery('agents', getAgents);

  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case 'research':
        return <Psychology />;
      case 'signal':
        return <TrendingUp />;
      case 'execution':
        return <AccountBalance />;
      case 'meta':
        return <Monitor />;
      default:
        return <Psychology />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'unhealthy':
        return 'error';
      default:
        return 'warning';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle />;
      case 'unhealthy':
        return <Error />;
      default:
        return <Warning />;
    }
  };

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
          Agents
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        Agents
      </Typography>

      <Grid container spacing={3}>
        {agents && Object.entries(agents).map(([agentName, agentData]) => (
          <Grid item xs={12} md={6} key={agentName}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  {getAgentIcon(agentName)}
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ textTransform: 'capitalize', fontWeight: 'bold' }}>
                      {agentName} Agent
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {agentName === 'research' && 'Market research and data analysis'}
                      {agentName === 'signal' && 'Trading signal generation'}
                      {agentName === 'execution' && 'Trade execution and management'}
                      {agentName === 'meta' && 'System coordination and oversight'}
                    </Typography>
                  </Box>
                  <Chip
                    icon={getStatusIcon(agentData?.health?.status || 'unknown')}
                    label={agentData?.health?.status || 'unknown'}
                    color={getStatusColor(agentData?.health?.status || 'unknown')}
                    variant="outlined"
                  />
                </Box>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="subtitle2">Agent Details</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Status:</strong> {agentData?.health?.status || 'Unknown'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Last Check:</strong> {agentData?.health?.timestamp || 'Unknown'}
                      </Typography>
                      {agentData?.health?.details && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            <strong>Details:</strong>
                          </Typography>
                          <pre style={{ fontSize: '0.75rem', color: '#b0b0b0' }}>
                            {JSON.stringify(agentData.health.details, null, 2)}
                          </pre>
                        </Box>
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>

                {agentData?.error && (
                  <Box sx={{ mt: 2, p: 2, backgroundColor: 'error.dark', borderRadius: 1 }}>
                    <Typography variant="body2" color="error.light">
                      <strong>Error:</strong> {agentData.error}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Agents; 