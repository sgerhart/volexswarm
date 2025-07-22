import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  agent: string;
  message: string;
}

const AgentLogs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: '1',
      timestamp: '2024-01-15T10:30:00Z',
      level: 'info',
      agent: 'Research Agent',
      message: 'Market analysis completed for BTC/USDT pair',
    },
    {
      id: '2',
      timestamp: '2024-01-15T10:29:30Z',
      level: 'info',
      agent: 'Signal Agent',
      message: 'Generated buy signal for ETH/USDT based on RSI divergence',
    },
    {
      id: '3',
      timestamp: '2024-01-15T10:29:00Z',
      level: 'warning',
      agent: 'Execution Agent',
      message: 'Order execution delayed due to high market volatility',
    },
    {
      id: '4',
      timestamp: '2024-01-15T10:28:30Z',
      level: 'info',
      agent: 'Meta Agent',
      message: 'Portfolio rebalancing initiated',
    },
    {
      id: '5',
      timestamp: '2024-01-15T10:28:00Z',
      level: 'error',
      agent: 'Monitor Agent',
      message: 'Failed to connect to Binance API - retrying in 30 seconds',
    },
    {
      id: '6',
      timestamp: '2024-01-15T10:27:30Z',
      level: 'info',
      agent: 'Optimize Agent',
      message: 'Strategy parameters optimized based on recent performance',
    },
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [filterLevel, setFilterLevel] = useState<string>('all');

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <InfoIcon color="info" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="action" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'info':
        return 'info';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.agent.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLevel = filterLevel === 'all' || log.level === filterLevel;
    return matchesSearch && matchesLevel;
  });

  const clearSearch = () => {
    setSearchTerm('');
    setFilterLevel('all');
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" sx={{ color: 'primary.main' }}>
            Agent Logs
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip label={`${logs.length} total`} size="small" />
            <Chip label={`${filteredLogs.length} filtered`} size="small" color="primary" />
          </Box>
        </Box>

        {/* Search and Filter */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <TextField
            size="small"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: searchTerm && (
                <InputAdornment position="end">
                  <IconButton size="small" onClick={clearSearch}>
                    <ClearIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ flexGrow: 1 }}
          />
          <Box sx={{ display: 'flex', gap: 1 }}>
            {['all', 'info', 'warning', 'error'].map((level) => (
              <Chip
                key={level}
                label={level.toUpperCase()}
                size="small"
                color={filterLevel === level ? 'primary' : 'default'}
                onClick={() => setFilterLevel(level)}
                clickable
              />
            ))}
          </Box>
        </Box>

        {/* Logs List */}
        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
          <List dense>
            {filteredLogs.map((log) => (
              <ListItem
                key={log.id}
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1,
                  backgroundColor: 'background.paper',
                }}
              >
                <ListItemIcon>
                  {getLevelIcon(log.level)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {log.agent}
                      </Typography>
                      <Chip
                        label={log.level.toUpperCase()}
                        color={getLevelColor(log.level) as any}
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                      </Typography>
                    </Box>
                  }
                  secondary={log.message}
                  secondaryTypographyProps={{
                    sx: { color: 'text.primary', mt: 0.5 },
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>

        {filteredLogs.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              No logs found matching your criteria
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AgentLogs; 