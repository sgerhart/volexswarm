import React, { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Card,
  CardContent,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  ShowChart as ChartIcon,
  AccountBalance as TradingIcon,
  Psychology as AiIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Refresh as RefreshIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import AgentStatus from './AgentStatus';
import SystemMetrics from './SystemMetrics';
import TradingOverview from './TradingOverview';
import AgentLogs from './AgentLogs';

const Dashboard: React.FC = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeComponent, setActiveComponent] = useState('dashboard');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, component: 'dashboard' },
    { text: 'Trading', icon: <TradingIcon />, component: 'trading' },
    { text: 'Analytics', icon: <ChartIcon />, component: 'analytics' },
    { text: 'AI Research', icon: <AiIcon />, component: 'research' },
    { text: 'Settings', icon: <SettingsIcon />, component: 'settings' },
  ];

  const renderComponent = () => {
    switch (activeComponent) {
      case 'dashboard':
        return (
          <Box>
            <Typography variant="h4" gutterBottom sx={{ color: 'primary.main', mb: 3 }}>
              VolexSwarm Dashboard
            </Typography>
            
            <AgentStatus />
            
            <Box sx={{ mt: 4 }}>
              <SystemMetrics />
            </Box>
            
            <Box sx={{ mt: 4 }}>
              <TradingOverview />
            </Box>
            
            <Box sx={{ mt: 4 }}>
              <AgentLogs />
            </Box>
          </Box>
        );
      case 'trading':
        return (
          <Box>
            <Typography variant="h4" gutterBottom sx={{ color: 'primary.main' }}>
              Trading Interface
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Advanced trading interface coming soon...
            </Typography>
          </Box>
        );
      case 'analytics':
        return (
          <Box>
            <Typography variant="h4" gutterBottom sx={{ color: 'primary.main' }}>
              Analytics & Charts
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Performance analytics and charts coming soon...
            </Typography>
          </Box>
        );
      case 'research':
        return (
          <Box>
            <Typography variant="h4" gutterBottom sx={{ color: 'primary.main' }}>
              AI Research
            </Typography>
            <Typography variant="body1" color="text.secondary">
              AI-powered market research and insights coming soon...
            </Typography>
          </Box>
        );
      case 'settings':
        return (
          <Box>
            <Typography variant="h4" gutterBottom sx={{ color: 'primary.main' }}>
              System Settings
            </Typography>
            <Typography variant="body1" color="text.secondary">
              System configuration and management coming soon...
            </Typography>
          </Box>
        );
      default:
        return null;
    }
  };

  const drawer = (
    <Box sx={{ width: 250 }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 'bold' }}>
          VolexSwarm
        </Typography>
        <Typography variant="caption" color="text.secondary">
          AI Trading Platform
        </Typography>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem
            key={item.text}
            onClick={() => {
              setActiveComponent(item.component);
              if (isMobile) setDrawerOpen(false);
            }}
            sx={{
              cursor: 'pointer',
              backgroundColor: activeComponent === item.component ? 'primary.main' : 'transparent',
              color: activeComponent === item.component ? 'primary.contrastText' : 'inherit',
              '&:hover': {
                backgroundColor: activeComponent === item.component ? 'primary.dark' : 'action.hover',
              },
            }}
          >
            <ListItemIcon sx={{ color: 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            VolexSwarm - AI Trading System
          </Typography>
          <IconButton color="inherit">
            <RefreshIcon />
          </IconButton>
          <IconButton color="inherit">
            <NotificationsIcon />
          </IconButton>
          <Chip
            label="System Online"
            color="success"
            size="small"
            sx={{ ml: 2 }}
          />
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: 250 }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={drawerOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { width: 250, backgroundColor: 'background.paper' },
          }}
        >
          {drawer}
        </Drawer>
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { width: 250, backgroundColor: 'background.paper' },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - 250px)` },
          mt: 8,
        }}
      >
        <Container maxWidth="xl">
          {renderComponent()}
        </Container>
      </Box>
    </Box>
  );
};

export default Dashboard; 