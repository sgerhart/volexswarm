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
import { fetchAllAgentsStatus, Agent } from '../services/agentService';
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



const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);



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
      // Fetch real agent status from actual running agents
      const realAgents = await fetchAllAgentsStatus();
      setAgents(realAgents);
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
          ? { ...agent, status: (action === 'stop' ? 'stopped' : 'starting') as Agent['status'] }
          : agent
      ));
      
      // Simulate status update after action
      setTimeout(() => {
        setAgents(prev => prev.map(agent => 
          agent.id === agentId 
            ? { ...agent, status: (action === 'stop' ? 'stopped' : 'healthy') as Agent['status'] }
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
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Agents
            </Typography>
            <Typography variant="h4" sx={{ color: 'primary.main' }}>
              {agents.length}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Healthy
            </Typography>
            <Typography variant="h4" sx={{ color: 'success.main' }}>
              {agents.filter(a => a.status === 'healthy').length}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Issues
            </Typography>
            <Typography variant="h4" sx={{ color: 'error.main' }}>
              {agents.filter(a => a.status !== 'healthy').length}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
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
      </Box>

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
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ flex: 1, minWidth: 200 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Version
                  </Typography>
                  <Typography variant="body1">{selectedAgent.version}</Typography>
                </Box>
                <Box sx={{ flex: 1, minWidth: 200 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Port
                  </Typography>
                  <Typography variant="body1">{selectedAgent.port}</Typography>
                </Box>
                <Box sx={{ flex: 1, minWidth: 200 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Memory Usage
                  </Typography>
                  <Typography variant="body1">{selectedAgent.memory}</Typography>
                </Box>
                <Box sx={{ flex: 1, minWidth: 200 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    CPU Usage
                  </Typography>
                  <Typography variant="body1">{selectedAgent.cpu}</Typography>
                </Box>
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Endpoints
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {selectedAgent.endpoints.map((endpoint) => (
                    <Chip key={endpoint} label={endpoint} size="small" />
                  ))}
                </Box>
              </Box>
              <Box sx={{ mt: 2 }}>
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
              </Box>
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