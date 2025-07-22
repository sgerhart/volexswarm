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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as HealthyIcon,
  Error as UnhealthyIcon,
  Help as UnknownIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

interface Agent {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  lastSeen: string;
  endpoint: string;
}

interface AgentStatusCardProps {
  agent: Agent;
}

const AgentStatusCard: React.FC<AgentStatusCardProps> = ({ agent }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

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

  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setLastChecked(new Date());
    } catch (error) {
      console.error('Failed to refresh agent status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card sx={{ height: '100%', position: 'relative' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getStatusIcon(agent.status)}
            <Typography variant="h6" component="div">
              {agent.name}
            </Typography>
          </Box>
          <Tooltip title="Refresh status">
            <IconButton
              size="small"
              onClick={handleRefresh}
              disabled={isLoading}
              sx={{ color: 'primary.main' }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {isLoading && (
          <LinearProgress sx={{ mb: 2 }} />
        )}

        <Box sx={{ mb: 2 }}>
          <Chip
            label={agent.status.toUpperCase()}
            color={getStatusColor(agent.status) as any}
            size="small"
            sx={{ fontWeight: 'bold' }}
          />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <ScheduleIcon fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary">
            Last seen: {formatDistanceToNow(new Date(agent.lastSeen), { addSuffix: true })}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Endpoint: {agent.endpoint}
          </Typography>
        </Box>

        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Typography variant="caption" color="text.secondary">
            Last checked: {formatDistanceToNow(lastChecked, { addSuffix: true })}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default AgentStatusCard; 