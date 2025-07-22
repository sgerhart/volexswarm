import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress,
  Tooltip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Warning as WarningIcon,
  CheckCircle as HealthyIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

interface Agent {
  id: string;
  name: string;
  port: number;
  status: 'healthy' | 'unhealthy' | 'starting' | 'stopped' | 'error';
  lastSeen: string;
  version: string;
  uptime: string;
  memory: string;
  cpu: string;
  endpoints: string[];
  dependencies: string[];
}

const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Define all our agents
  const agentDefinitions: Agent[] = [
    {
      id: 'vault',
      name: 'Vault',
      port: 8200,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '1.15.0',
      uptime: '2d 14h 32m',
      memory: '45.2 MB',
      cpu: '2.1%',
      endpoints: ['/v1/sys/health', '/v1/sys/leader'],
      dependencies: [],
    },
    {
      id: 'db',
      name: 'TimescaleDB',
      port: 5432,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '2.11.0',
      uptime: '2d 14h 32m',
      memory: '156.7 MB',
      cpu: '8.3%',
      endpoints: ['/health', '/metrics'],
      dependencies: [],
    },
    {
      id: 'redis',
      name: 'Redis',
      port: 6379,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '7.2.0',
      uptime: '2d 14h 32m',
      memory: '23.1 MB',
      cpu: '1.2%',
      endpoints: ['PING', 'INFO'],
      dependencies: [],
    },
    {
      id: 'research',
      name: 'Research Agent',
      port: 8001,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '1.0.0',
      uptime: '2d 14h 32m',
      memory: '89.4 MB',
      cpu: '12.7%',
      endpoints: ['/health', '/research', '/sentiment'],
      dependencies: ['vault', 'db'],
    },
    {
      id: 'execution',
      name: 'Execution Agent',
      port: 8002,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '1.0.0',
      uptime: '2d 14h 32m',
      memory: '134.2 MB',
      cpu: '15.8%',
      endpoints: ['/health', '/orders', '/positions'],
      dependencies: ['vault', 'db'],
    },
    {
      id: 'signal',
      name: 'Signal Agent',
      port: 8003,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '1.0.0',
      uptime: '2d 14h 32m',
      memory: '167.8 MB',
      cpu: '18.9%',
      endpoints: ['/health', '/signals', '/indicators'],
      dependencies: ['vault', 'db'],
    },
    {
      id: 'meta',
      name: 'Meta Agent',
      port: 8004,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '1.0.0',
      uptime: '2d 14h 32m',
      memory: '78.3 MB',
      cpu: '9.4%',
      endpoints: ['/health', '/orchestrate', '/status'],
      dependencies: ['research', 'execution', 'signal', 'strategy'],
    },
    {
      id: 'strategy',
      name: 'Strategy Agent',
      port: 8011,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '1.0.0',
      uptime: '2d 14h 32m',
      memory: '112.6 MB',
      cpu: '11.3%',
      endpoints: ['/health', '/strategies', '/templates'],
      dependencies: ['vault', 'db'],
    },
    {
      id: 'risk',
      name: 'Risk Agent',
      port: 8009,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '1.0.0',
      uptime: '2d 14h 32m',
      memory: '95.7 MB',
      cpu: '7.8%',
      endpoints: ['/health', '/risk', '/limits'],
      dependencies: ['vault', 'db'],
    },
    {
      id: 'compliance',
      name: 'Compliance Agent',
      port: 8010,
      status: 'healthy',
      lastSeen: new Date().toISOString(),
      version: '1.0.0',
      uptime: '2d 14h 32m',
      memory: '67.2 MB',
      cpu: '5.2%',
      endpoints: ['/health', '/compliance', '/audit'],
      dependencies: ['vault', 'db'],
    },
  ];

  useEffect(() => {
    fetchAgentStatus();
    
    if (autoRefresh) {
      const interval = setInterval(fetchAgentStatus, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchAgentStatus = async () => {
    setLoading(true);
    try {
      // Simulate fetching real agent status
      // In production, this would make actual API calls to each agent
      const updatedAgents: Agent[] = agentDefinitions.map(agent => ({
        ...agent,
        status: Math.random() > 0.1 ? 'healthy' : 'unhealthy' as const, // 90% healthy
        lastSeen: new Date().toISOString(),
        memory: `${Math.floor(Math.random() * 200 + 50)}.${Math.floor(Math.random() * 10)} MB`,
        cpu: `${(Math.random() * 20 + 1).toFixed(1)}%`,
      }));
      
      setAgents(updatedAgents);
    } catch (error) {
      console.error('Error fetching agent status:', error);
    } finally {
      setLoading(false);
    }
  };

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
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon />;
      case 'unhealthy':
        return <ErrorIcon />;
      case 'starting':
        return <CircularProgress size={16} />;
      case 'stopped':
        return <StopIcon />;
      case 'error':
        return <WarningIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const handleAgentAction = async (agentId: string, action: 'start' | 'stop' | 'restart') => {
    try {
      // In production, this would make actual API calls to control agents
      console.log(`${action} agent: ${agentId}`);
      
      // Simulate action
      setAgents(prev => prev.map(agent => 
        agent.id === agentId 
          ? { ...agent, status: action === 'stop' ? 'stopped' : 'starting' as const }
          : agent
      ));
      
      // Simulate status update after action
      setTimeout(() => {
        setAgents(prev => prev.map(agent => 
          agent.id === agentId 
            ? { ...agent, status: action === 'stop' ? 'stopped' : 'healthy' as const }
            : agent
        ));
      }, 2000);
      
    } catch (error) {
      console.error(`Error ${action}ing agent ${agentId}:`, error);
    }
  };

  const handleViewDetails = (agent: Agent) => {
    setSelectedAgent(agent);
    setDialogOpen(true);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ color: 'primary.main' }}>
          Agent Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                color="primary"
              />
            }
            label="Auto Refresh"
          />
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchAgentStatus}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* System Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Agents
              </Typography>
              <Typography variant="h4" sx={{ color: 'primary.main' }}>
                {agents.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Healthy
              </Typography>
              <Typography variant="h4" sx={{ color: 'success.main' }}>
                {agents.filter(a => a.status === 'healthy').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Issues
              </Typography>
              <Typography variant="h4" sx={{ color: 'error.main' }}>
                {agents.filter(a => a.status !== 'healthy').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                System Status
              </Typography>
              <Chip
                label={agents.every(a => a.status === 'healthy') ? 'All Systems Operational' : 'Issues Detected'}
                color={agents.every(a => a.status === 'healthy') ? 'success' : 'error'}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Agents Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Agent Status
          </Typography>
          <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Agent</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Port</TableCell>
                  <TableCell>Memory</TableCell>
                  <TableCell>CPU</TableCell>
                  <TableCell>Uptime</TableCell>
                  <TableCell>Last Seen</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {agents.map((agent) => (
                  <TableRow key={agent.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {agent.name}
                        </Typography>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => handleViewDetails(agent)}
                          >
                            <SettingsIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(agent.status)}
                        label={agent.status}
                        color={getStatusColor(agent.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{agent.port}</TableCell>
                    <TableCell>{agent.memory}</TableCell>
                    <TableCell>{agent.cpu}</TableCell>
                    <TableCell>{agent.uptime}</TableCell>
                    <TableCell>
                      {new Date(agent.lastSeen).toLocaleTimeString()}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="Start">
                          <IconButton
                            size="small"
                            onClick={() => handleAgentAction(agent.id, 'start')}
                            disabled={agent.status === 'healthy'}
                          >
                            <StartIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Stop">
                          <IconButton
                            size="small"
                            onClick={() => handleAgentAction(agent.id, 'stop')}
                            disabled={agent.status === 'stopped'}
                          >
                            <StopIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Restart">
                          <IconButton
                            size="small"
                            onClick={() => handleAgentAction(agent.id, 'restart')}
                          >
                            <RefreshIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Agent Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Agent Details: {selectedAgent?.name}
        </DialogTitle>
        <DialogContent>
          {selectedAgent && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Version
                  </Typography>
                  <Typography variant="body1">{selectedAgent.version}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Port
                  </Typography>
                  <Typography variant="body1">{selectedAgent.port}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Memory Usage
                  </Typography>
                  <Typography variant="body1">{selectedAgent.memory}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    CPU Usage
                  </Typography>
                  <Typography variant="body1">{selectedAgent.cpu}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Endpoints
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedAgent.endpoints.map((endpoint) => (
                      <Chip key={endpoint} label={endpoint} size="small" />
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Dependencies
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedAgent.dependencies.length > 0 ? (
                      selectedAgent.dependencies.map((dep) => (
                        <Chip key={dep} label={dep} size="small" color="primary" />
                      ))
                    ) : (
                      <Typography variant="body2" color="textSecondary">
                        No dependencies
                      </Typography>
                    )}
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentManagement; 