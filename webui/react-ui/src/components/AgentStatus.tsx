import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Grid,
  Alert,
  Button,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as HealthyIcon,
  Error as UnhealthyIcon,
  Help as UnknownIcon,
  Schedule as ScheduleIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Settings as ConfigIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { apiService } from '../services/api';

interface Agent {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  lastSeen: string;
  endpoint: string;
  port: number;
  description: string;
  isRunning: boolean;
}

const AgentStatus: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);

  // Define all VolexSwarm agents
  const allAgents: Omit<Agent, 'status' | 'lastSeen' | 'isRunning'>[] = [
    {
      name: 'Research Agent',
      endpoint: 'http://localhost:8001/health',
      port: 8001,
      description: 'AI-powered market research and analysis'
    },
    {
      name: 'Execution Agent',
      endpoint: 'http://localhost:8002/health',
      port: 8002,
      description: 'Trade execution and order management'
    },
    {
      name: 'Signal Agent',
      endpoint: 'http://localhost:8003/health',
      port: 8003,
      description: 'Trading signal generation and analysis'
    },
    {
      name: 'Meta Agent',
      endpoint: 'http://localhost:8004/health',
      port: 8004,
      description: 'Orchestration and coordination of all agents'
    },
    {
      name: 'Optimize Agent',
      endpoint: 'http://localhost:8006/health',
      port: 8006,
      description: 'Portfolio optimization and strategy refinement'
    },
    {
      name: 'Monitor Agent',
      endpoint: 'http://localhost:8007/health',
      port: 8007,
      description: 'System monitoring and alerting'
    },
    {
      name: 'Backtest Agent',
      endpoint: 'http://localhost:8008/health',
      port: 8008,
      description: 'Strategy backtesting and validation'
    },
    {
      name: 'Compliance Agent',
      endpoint: 'http://localhost:8009/health',
      port: 8009,
      description: 'Regulatory compliance and risk monitoring'
    },
    {
      name: 'Risk Agent',
      endpoint: 'http://localhost:8010/health',
      port: 8010,
      description: 'Risk assessment and management'
    },
    {
      name: 'Strategy Agent',
      endpoint: 'http://localhost:8011/health',
      port: 8011,
      description: 'Strategy development and management'
    },
  ];

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
        return <HealthyIcon color="success" />;
      case 'unhealthy':
        return <UnhealthyIcon color="error" />;
      default:
        return <UnknownIcon color="warning" />;
    }
  };

  const checkAgentHealth = async (agentName: string): Promise<Agent> => {
    try {
      const healthData = await apiService.getAgentHealth(agentName);
      return {
        name: healthData.name,
        status: healthData.status,
        lastSeen: healthData.lastSeen,
        endpoint: healthData.endpoint,
        port: allAgents.find(a => a.name === healthData.name)?.port || 0,
        description: allAgents.find(a => a.name === healthData.name)?.description || '',
        isRunning: healthData.status === 'healthy',
      };
    } catch (error) {
      const agent = allAgents.find(a => a.name === agentName);
      return {
        name: agentName,
        status: 'unknown',
        lastSeen: new Date().toISOString(),
        endpoint: agent?.endpoint || '',
        port: agent?.port || 0,
        description: agent?.description || '',
        isRunning: false,
      };
    }
  };

  const refreshAllAgents = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const agentNames = allAgents.map(agent => agent.name);
      const healthPromises = agentNames.map(name => checkAgentHealth(name));
      const results = await Promise.allSettled(healthPromises);
      
      const updatedAgents = results.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value;
        } else {
          const agent = allAgents[index];
          return {
            name: agent.name,
            status: 'unknown' as const,
            lastSeen: new Date().toISOString(),
            endpoint: agent.endpoint,
            port: agent.port,
            description: agent.description,
            isRunning: false,
          };
        }
      });
      
      setAgents(updatedAgents);
      setLastChecked(new Date());
    } catch (error) {
      setError('Failed to refresh agent status');
      console.error('Failed to refresh agents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartAgent = async (agentName: string) => {
    // TODO: Implement agent start functionality
    console.log(`Starting agent: ${agentName}`);
  };

  const handleStopAgent = async (agentName: string) => {
    // TODO: Implement agent stop functionality
    console.log(`Stopping agent: ${agentName}`);
  };

  const handleConfigureAgent = async (agentName: string) => {
    // TODO: Implement agent configuration
    console.log(`Configuring agent: ${agentName}`);
  };

  useEffect(() => {
    refreshAllAgents();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(refreshAllAgents, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ color: 'primary.main', fontWeight: 'bold' }}>
          Agent Status
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={refreshAllAgents}
            disabled={isLoading}
          >
            Refresh All
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {isLoading && (
        <LinearProgress sx={{ mb: 2 }} />
      )}

      <Grid container spacing={2}>
        {agents.map((agent) => (
          <Grid item xs={12} sm={6} md={4} key={agent.name}>
            <Card sx={{ height: '100%', position: 'relative' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(agent.status)}
                    <Typography variant="h6" component="div">
                      {agent.name}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="Start Agent">
                      <IconButton
                        size="small"
                        onClick={() => handleStartAgent(agent.name)}
                        disabled={agent.isRunning}
                        sx={{ color: 'success.main' }}
                      >
                        <StartIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Stop Agent">
                      <IconButton
                        size="small"
                        onClick={() => handleStopAgent(agent.name)}
                        disabled={!agent.isRunning}
                        sx={{ color: 'error.main' }}
                      >
                        <StopIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Configure Agent">
                      <IconButton
                        size="small"
                        onClick={() => handleConfigureAgent(agent.name)}
                        sx={{ color: 'primary.main' }}
                      >
                        <ConfigIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Chip
                    label={agent.status.toUpperCase()}
                    color={getStatusColor(agent.status) as any}
                    size="small"
                    sx={{ fontWeight: 'bold' }}
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {agent.description}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <ScheduleIcon fontSize="small" color="action" />
                  <Typography variant="body2" color="text.secondary">
                    Last seen: {formatDistanceToNow(new Date(agent.lastSeen), { addSuffix: true })}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Port: {agent.port}
                  </Typography>
                </Box>

                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  <Typography variant="caption" color="text.secondary">
                    Last checked: {formatDistanceToNow(lastChecked, { addSuffix: true })}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default AgentStatus; 