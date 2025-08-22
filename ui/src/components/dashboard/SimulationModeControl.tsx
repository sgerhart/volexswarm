import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Switch,
  FormControlLabel,
  Alert,
  Chip,
  Divider
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Settings as SettingsIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface SimulationModeControlProps {
  open: boolean;
  onClose: () => void;
}

interface TradingConfig {
  mode: string;
  simulation_balance: number;
  max_simulation_risk: number;
  real_trading_enabled: boolean;
  simulation_accounts: string[];
  real_accounts: string[];
  safety_checks_enabled: boolean;
  max_position_size: number;
  emergency_stop_enabled: boolean;
  // Portfolio Collection Settings
  portfolio_collection_enabled: boolean;
  collection_frequency_minutes: number;
  change_threshold_percent: number;
  max_collections_per_hour: number;
  data_retention_days: number;
  enable_compression: boolean;
  // Risk Management Settings
  max_portfolio_risk: number;
  max_drawdown: number;
  daily_loss_limit: number;
  weekly_loss_limit: number;
  monthly_loss_limit: number;
  max_single_position_size: number;
  max_sector_exposure: number;
  correlation_limit: number;
  leverage_limit: number;
  default_stop_loss: number;
  default_take_profit: number;
  trailing_stop_enabled: boolean;
  trailing_stop_distance: number;
}

const SimulationModeControl: React.FC<SimulationModeControlProps> = ({ open, onClose }) => {
  const [config, setConfig] = useState<TradingConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedConfig, setEditedConfig] = useState<TradingConfig | null>(null);

  const tradingModes = [
    { value: 'simulation', label: '🔬 Simulation Mode', description: 'Safe testing with fake orders' },
    { value: 'real_trading', label: '💰 Real Trading Mode', description: 'Live trading with real money' },
    { value: 'hybrid', label: '🔄 Hybrid Mode', description: 'Both simulation and real trading' },
    { value: 'sandbox', label: '🏖️ Sandbox Mode', description: 'Strategy testing environment' },
    { value: 'backtest', label: '📊 Backtest Mode', description: 'Historical strategy testing' }
  ];

  useEffect(() => {
    if (open) {
      loadCurrentConfig();
    }
  }, [open]);

  const loadCurrentConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8002/api/execution/trading-config');
      if (!response.ok) {
        throw new Error('Failed to load trading configuration');
      }
      
      const data = await response.json();
      
      // Ensure all required fields have default values
      const configWithDefaults = {
        ...data.config,
        // Portfolio Collection Settings
        portfolio_collection_enabled: data.config.portfolio_collection_enabled ?? true,
        collection_frequency_minutes: data.config.collection_frequency_minutes ?? 15,
        change_threshold_percent: data.config.change_threshold_percent ?? 2.0,
        max_collections_per_hour: data.config.max_collections_per_hour ?? 60,
        data_retention_days: data.config.data_retention_days ?? 30,
        enable_compression: data.config.enable_compression ?? true,
        // Risk Management Settings
        max_portfolio_risk: data.config.max_portfolio_risk ?? 0.05,
        max_drawdown: data.config.max_drawdown ?? 0.10,
        daily_loss_limit: data.config.daily_loss_limit ?? 1000,
        weekly_loss_limit: data.config.weekly_loss_limit ?? 5000,
        monthly_loss_limit: data.config.monthly_loss_limit ?? 20000,
        max_single_position_size: data.config.max_single_position_size ?? 0.20,
        max_sector_exposure: data.config.max_sector_exposure ?? 0.30,
        correlation_limit: data.config.correlation_limit ?? 0.70,
        leverage_limit: data.config.leverage_limit ?? 1.0,
        default_stop_loss: data.config.default_stop_loss ?? 0.05,
        default_take_profit: data.config.default_take_profit ?? 0.15,
        trailing_stop_enabled: data.config.trailing_stop_enabled ?? true,
        trailing_stop_distance: data.config.trailing_stop_distance ?? 0.03
      };
      
      setConfig(configWithDefaults);
      setEditedConfig(configWithDefaults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleModeChange = async (newMode: string) => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const response = await fetch('http://localhost:8002/api/execution/switch-mode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: newMode }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to switch trading mode');
      }
      
      const data = await response.json();
      if (data.success) {
        setSuccess(`Successfully switched to ${newMode} mode`);
        await loadCurrentConfig(); // Reload to get updated config
      } else {
        throw new Error(data.error || 'Failed to switch mode');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch mode');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigUpdate = async () => {
    if (!editedConfig) return;
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const response = await fetch('http://localhost:8002/api/execution/update-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editedConfig),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update configuration');
      }
      
      const data = await response.json();
      if (data.success) {
        setSuccess('Configuration updated successfully');
        setEditMode(false);
        await loadCurrentConfig(); // Reload to get updated config
      } else {
        throw new Error(data.error || 'Failed to update configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update configuration');
    } finally {
      setLoading(false);
    }
  };

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'simulation': return <PlayIcon color="success" />;
      case 'real_trading': return <WarningIcon color="error" />;
      case 'hybrid': return <InfoIcon color="info" />;
      case 'sandbox': return <CheckIcon color="primary" />;
      case 'backtest': return <InfoIcon color="secondary" />;
      default: return <InfoIcon />;
    }
  };

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'simulation': return 'success';
      case 'real_trading': return 'error';
      case 'hybrid': return 'info';
      case 'sandbox': return 'primary';
      case 'backtest': return 'secondary';
      default: return 'default';
    }
  };

  if (!config) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>Simulation Mode Control</DialogTitle>
        <DialogContent>
          <Box display="flex" justifyContent="center" p={3}>
            {loading ? (
              <Typography>Loading configuration...</Typography>
            ) : (
              <Typography color="error">Failed to load configuration</Typography>
            )}
          </Box>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <SettingsIcon />
          <Typography variant="h6">Simulation Mode Control</Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        {/* Current Mode Display */}
        <Card sx={{ mb: 3, bgcolor: 'background.paper' }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              {getModeIcon(config.mode)}
              <Typography variant="h6">
                Current Mode: {config.mode.replace('_', ' ').toUpperCase()}
              </Typography>
              <Chip 
                label={config.mode} 
                color={getModeColor(config.mode) as any}
                variant="outlined"
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {tradingModes.find(m => m.value === config.mode)?.description}
            </Typography>
            
            {config.mode === 'real_trading' && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                ⚠️ Real trading mode is active. Real money will be used for trades.
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Mode Selection */}
        <Card sx={{ mb: 3, bgcolor: 'background.paper' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Switch Trading Mode
            </Typography>
            
            <Box display="flex" flexWrap="wrap" gap={1}>
              {tradingModes.map((mode) => (
                <Card
                  key={mode.value}
                  sx={{
                    minWidth: 200,
                    cursor: 'pointer',
                    border: config.mode === mode.value ? 2 : 1,
                    borderColor: config.mode === mode.value ? 'primary.main' : 'divider',
                    '&:hover': { borderColor: 'primary.main' }
                  }}
                  onClick={() => handleModeChange(mode.value)}
                >
                  <CardContent sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle1" gutterBottom>
                      {mode.label}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {mode.description}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Configuration Settings */}
        <Card sx={{ bgcolor: 'background.paper' }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
              <Typography variant="h6">
                Configuration Settings
              </Typography>
              <Button
                variant={editMode ? "contained" : "outlined"}
                onClick={() => setEditMode(!editMode)}
                startIcon={editMode ? <CheckIcon /> : <SettingsIcon />}
              >
                {editMode ? "Save Changes" : "Edit Settings"}
              </Button>
            </Box>

            {editMode && editedConfig ? (
              <Box>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Simulation Balance ($)"
                    type="number"
                    value={editedConfig.simulation_balance}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      simulation_balance: parseFloat(e.target.value) || 0
                    })}
                    fullWidth
                  />
                  
                  <TextField
                    label="Max Risk per Trade (%)"
                    type="number"
                    value={editedConfig.max_simulation_risk * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      max_simulation_risk: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                  />
                  
                  <TextField
                    label="Max Position Size (%)"
                    type="number"
                    value={editedConfig.max_position_size * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      max_position_size: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                  />
                </Box>

                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={editedConfig.safety_checks_enabled}
                        onChange={(e) => setEditedConfig({
                          ...editedConfig,
                          safety_checks_enabled: e.target.checked
                        })}
                      />
                    }
                    label="Safety Checks Enabled"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={editedConfig.emergency_stop_enabled}
                        onChange={(e) => setEditedConfig({
                          ...editedConfig,
                          emergency_stop_enabled: e.target.checked
                        })}
                      />
                    }
                    label="Emergency Stop Enabled"
                  />
                </Box>

                {/* Portfolio Collection Settings */}
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Portfolio Collection Settings
                </Typography>
                
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={editedConfig.portfolio_collection_enabled}
                        onChange={(e) => setEditedConfig({
                          ...editedConfig,
                          portfolio_collection_enabled: e.target.checked
                        })}
                      />
                    }
                    label="Automatic Collection Enabled"
                  />
                  
                  <TextField
                    label="Collection Frequency (minutes)"
                    type="number"
                    value={editedConfig.collection_frequency_minutes}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      collection_frequency_minutes: parseInt(e.target.value) || 15
                    })}
                    fullWidth
                    inputProps={{ min: 1, max: 1440 }}
                    helperText="1-1440 minutes (1 min to 24 hours)"
                  />
                </Box>

                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Change Threshold (%)"
                    type="number"
                    value={editedConfig.change_threshold_percent}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      change_threshold_percent: parseFloat(e.target.value) || 2.0
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0.1, max: 50 }}
                    helperText="Portfolio value change % to trigger collection"
                  />
                  
                  <TextField
                    label="Max Collections per Hour"
                    type="number"
                    value={editedConfig.max_collections_per_hour}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      max_collections_per_hour: parseInt(e.target.value) || 60
                    })}
                    fullWidth
                    inputProps={{ min: 1, max: 3600 }}
                    helperText="Limit hourly database writes"
                  />
                </Box>

                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Data Retention (days)"
                    type="number"
                    value={editedConfig.data_retention_days}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      data_retention_days: parseInt(e.target.value) || 30
                    })}
                    fullWidth
                    inputProps={{ min: 1, max: 365 }}
                    helperText="Days to keep detailed portfolio history"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={editedConfig.enable_compression}
                        onChange={(e) => setEditedConfig({
                          ...editedConfig,
                          enable_compression: e.target.checked
                        })}
                      />
                    }
                    label="Enable Data Compression"
                  />
                </Box>

                {/* Risk Management Settings */}
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Risk Management Settings
                </Typography>
                
                {/* Portfolio Risk Limits */}
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, color: 'primary.main' }}>
                  Portfolio Risk Limits
                </Typography>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Max Portfolio Risk (%)"
                    type="number"
                    value={editedConfig.max_portfolio_risk * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      max_portfolio_risk: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                    helperText="Total portfolio risk exposure limit"
                  />
                  
                  <TextField
                    label="Max Drawdown (%)"
                    type="number"
                    value={editedConfig.max_drawdown * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      max_drawdown: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                    helperText="Maximum allowed portfolio drawdown"
                  />
                </Box>
                
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Daily Loss Limit ($)"
                    type="number"
                    value={editedConfig.daily_loss_limit}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      daily_loss_limit: parseFloat(e.target.value) || 0
                    })}
                    fullWidth
                    inputProps={{ step: 1, min: 0 }}
                    helperText="Maximum daily loss in dollars"
                  />
                  
                  <TextField
                    label="Weekly Loss Limit ($)"
                    type="number"
                    value={editedConfig.weekly_loss_limit}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      weekly_loss_limit: parseFloat(e.target.value) || 0
                    })}
                    fullWidth
                    inputProps={{ step: 1, min: 0 }}
                    helperText="Maximum weekly loss in dollars"
                  />
                </Box>
                
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Monthly Loss Limit ($)"
                    type="number"
                    value={editedConfig.monthly_loss_limit}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      monthly_loss_limit: parseFloat(e.target.value) || 0
                    })}
                    fullWidth
                    inputProps={{ step: 1, min: 0 }}
                    helperText="Maximum monthly loss in dollars"
                  />
                </Box>
                
                {/* Position Risk Controls */}
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, color: 'primary.main' }}>
                  Position Risk Controls
                </Typography>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Max Single Position Size (%)"
                    type="number"
                    value={editedConfig.max_single_position_size * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      max_single_position_size: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                    helperText="Largest single position allowed"
                  />
                  
                  <TextField
                    label="Max Sector Exposure (%)"
                    type="number"
                    value={editedConfig.max_sector_exposure * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      max_sector_exposure: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                    helperText="Maximum exposure to any single sector"
                  />
                </Box>
                
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Correlation Limit (%)"
                    type="number"
                    value={editedConfig.correlation_limit * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      correlation_limit: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                    helperText="Maximum correlation between positions"
                  />
                  
                  <TextField
                    label="Leverage Limit (x)"
                    type="number"
                    value={editedConfig.leverage_limit}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      leverage_limit: parseFloat(e.target.value) || 1
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 1, max: 10 }}
                    helperText="Maximum leverage allowed (1x, 2x, 5x, etc.)"
                  />
                </Box>
                
                {/* Stop Loss & Take Profit */}
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, color: 'primary.main' }}>
                  Stop Loss & Take Profit
                </Typography>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <TextField
                    label="Default Stop Loss (%)"
                    type="number"
                    value={editedConfig.default_stop_loss * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      default_stop_loss: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                    helperText="Default stop loss for new positions"
                  />
                  
                  <TextField
                    label="Default Take Profit (%)"
                    type="number"
                    value={editedConfig.default_take_profit * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      default_take_profit: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                    helperText="Default take profit for new positions"
                  />
                </Box>
                
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={editedConfig.trailing_stop_enabled}
                        onChange={(e) => setEditedConfig({
                          ...editedConfig,
                          trailing_stop_enabled: e.target.checked
                        })}
                      />
                    }
                    label="Trailing Stop Enabled"
                  />
                  
                  <TextField
                    label="Trailing Stop Distance (%)"
                    type="number"
                    value={editedConfig.trailing_stop_distance * 100}
                    onChange={(e) => setEditedConfig({
                      ...editedConfig,
                      trailing_stop_distance: (parseFloat(e.target.value) || 0) / 100
                    })}
                    fullWidth
                    inputProps={{ step: 0.1, min: 0, max: 100 }}
                    helperText="Distance for trailing stop activation"
                    disabled={!editedConfig.trailing_stop_enabled}
                  />
                </Box>
                
                <Box display="flex" gap={1}>
                  <Button
                    variant="contained"
                    onClick={handleConfigUpdate}
                    disabled={loading}
                    startIcon={<CheckIcon />}
                  >
                    Update Configuration
                  </Button>
                  
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setEditMode(false);
                      setEditedConfig(config);
                    }}
                  >
                    Cancel
                  </Button>
                </Box>
              </Box>
            ) : (
              <Box>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <Typography variant="body2">
                    <strong>Simulation Balance:</strong> ${config.simulation_balance.toLocaleString()}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Max Risk per Trade:</strong> {(config.max_simulation_risk * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Max Position Size:</strong> {(config.max_position_size * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Safety Checks:</strong> {config.safety_checks_enabled ? '✅ Enabled' : '❌ Disabled'}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Emergency Stop:</strong> {config.emergency_stop_enabled ? '✅ Enabled' : '❌ Disabled'}
                  </Typography>
                </Box>

                {/* Portfolio Collection Settings Display */}
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Portfolio Collection Settings
                </Typography>
                
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <Typography variant="body2">
                    <strong>Automatic Collection:</strong> {config.portfolio_collection_enabled ? '✅ Enabled' : '❌ Disabled'}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Collection Frequency:</strong> {config.collection_frequency_minutes} minutes
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Change Threshold:</strong> {config.change_threshold_percent}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Max per Hour:</strong> {config.max_collections_per_hour}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Data Retention:</strong> {config.data_retention_days} days
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Compression:</strong> {config.enable_compression ? '✅ Enabled' : '❌ Disabled'}
                  </Typography>
                </Box>
                
                {/* Risk Management Settings Display */}
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Risk Management Settings
                </Typography>
                
                {/* Portfolio Risk Limits Display */}
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, color: 'primary.main' }}>
                  Portfolio Risk Limits
                </Typography>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <Typography variant="body2">
                    <strong>Max Portfolio Risk:</strong> {(config.max_portfolio_risk * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Max Drawdown:</strong> {(config.max_drawdown * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Daily Loss Limit:</strong> ${config.daily_loss_limit.toLocaleString()}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Weekly Loss Limit:</strong> ${config.weekly_loss_limit.toLocaleString()}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Monthly Loss Limit:</strong> ${config.monthly_loss_limit.toLocaleString()}
                  </Typography>
                </Box>
                
                {/* Position Risk Controls Display */}
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, color: 'primary.main' }}>
                  Position Risk Controls
                </Typography>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <Typography variant="body2">
                    <strong>Max Single Position:</strong> {(config.max_single_position_size * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Max Sector Exposure:</strong> {(config.max_sector_exposure * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Correlation Limit:</strong> {(config.correlation_limit * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Leverage Limit:</strong> {config.leverage_limit}x
                  </Typography>
                </Box>
                
                {/* Stop Loss & Take Profit Display */}
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, color: 'primary.main' }}>
                  Stop Loss & Take Profit
                </Typography>
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                  <Typography variant="body2">
                    <strong>Default Stop Loss:</strong> {(config.default_stop_loss * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Default Take Profit:</strong> {(config.default_take_profit * 100).toFixed(1)}%
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Trailing Stop:</strong> {config.trailing_stop_enabled ? '✅ Enabled' : '❌ Disabled'}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Trailing Distance:</strong> {(config.trailing_stop_distance * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SimulationModeControl;
