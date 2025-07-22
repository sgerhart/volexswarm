import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Error as UnhealthyIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { fetchAllAgentsStatus, AgentInfo } from '../services/systemService';

const AgentStatus: React.FC = () => {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchAgentStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const realAgents = await fetchAllAgentsStatus();
      setAgents(realAgents);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to fetch agent status');
      console.error('Error fetching agent status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentStatus();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAgentStatus();
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'unhealthy':
        return 'error';
      case 'starting':
        return 'warning';
      case 'stopped':
        return 'default';
      default:
        return 'error';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon />;
      case 'unhealthy':
        return <UnhealthyIcon />;
      case 'starting':
        return <WarningIcon />;
      case 'stopped':
        return <InfoIcon />;
      default:
        return <UnhealthyIcon />;
    }
  };

  const handleRefresh = () => {
    fetchAgentStatus();
  };

  const handleToggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
  };

  if (loading && agents.length === 0) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Agent Status
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Typography variant="caption" color="textSecondary">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
          <Button
            size="small"
            variant={autoRefresh ? 'contained' : 'outlined'}
            onClick={handleToggleAutoRefresh}
          >
            {autoRefresh ? 'Auto Refresh ON' : 'Auto Refresh OFF'}
          </Button>
          <IconButton onClick={handleRefresh} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2 }}>
        {agents.map((agent) => (
          <Card key={agent.id} sx={{ position: 'relative' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="h6" component="div">
                    {agent.name}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Port: {agent.port}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    icon={getStatusIcon(agent.status)}
                    label={agent.status}
                    color={getStatusColor(agent.status) as any}
                    size="small"
                  />
                  {loading && (
                    <CircularProgress size={16} />
                  )}
                </Box>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="textSecondary">
                    Version:
                  </Typography>
                  <Typography variant="body2">
                    {agent.version}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="textSecondary">
                    Memory:
                  </Typography>
                  <Typography variant="body2">
                    {agent.memory}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="textSecondary">
                    CPU:
                  </Typography>
                  <Typography variant="body2">
                    {agent.cpu}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="textSecondary">
                    Uptime:
                  </Typography>
                  <Typography variant="body2">
                    {agent.uptime}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="textSecondary">
                    Last Seen:
                  </Typography>
                  <Typography variant="body2">
                    {new Date(agent.lastSeen).toLocaleTimeString()}
                  </Typography>
                </Box>
              </Box>

              {agent.health && (
                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Health Details:
                  </Typography>
                  {agent.health.vault_connected !== undefined && (
                    <Chip
                      label={`Vault: ${agent.health.vault_connected ? 'Connected' : 'Disconnected'}`}
                      color={agent.health.vault_connected ? 'success' : 'error'}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  )}
                  {agent.health.database_connected !== undefined && (
                    <Chip
                      label={`DB: ${agent.health.database_connected ? 'Connected' : 'Disconnected'}`}
                      color={agent.health.database_connected ? 'success' : 'error'}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  )}
                  {agent.health.checks && (
                    <Box>
                      {agent.health.checks.database && (
                        <Chip
                          label={`DB Check: ${agent.health.checks.database.status}`}
                          color={agent.health.checks.database.status === 'healthy' ? 'success' : 'error'}
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      )}
                      {agent.health.checks.vault && (
                        <Chip
                          label={`Vault Check: ${agent.health.checks.vault.status}`}
                          color={agent.health.checks.vault.status === 'healthy' ? 'success' : 'error'}
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      )}
                    </Box>
                  )}
                </Box>
              )}

              <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Endpoints:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {agent.endpoints.map((endpoint, index) => (
                    <Chip
                      key={index}
                      label={endpoint}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>

              {agent.dependencies.length > 0 && (
                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Dependencies:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {agent.dependencies.map((dep, index) => (
                      <Chip
                        key={index}
                        label={dep}
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
};

export default AgentStatus; 