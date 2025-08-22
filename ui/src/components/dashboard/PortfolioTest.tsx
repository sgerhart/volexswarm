import React, { useEffect, useState } from 'react';
import { Card, CardContent, Typography, Button } from '@mui/material';
import agentService from '../../services/agentService';

const PortfolioTest: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolio = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🧪 PortfolioTest: Starting fetch...');
      const data = await agentService.getPortfolioData();
      console.log('🧪 PortfolioTest: Received data:', data);
      setPortfolioData(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('🧪 PortfolioTest: Error:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          🧪 Portfolio Data Test
        </Typography>
        
        <Button 
          variant="contained" 
          onClick={fetchPortfolio}
          disabled={loading}
          sx={{ mb: 2 }}
        >
          {loading ? 'Fetching...' : 'Fetch Portfolio Data'}
        </Button>

        {error && (
          <Typography color="error" sx={{ mb: 2 }}>
            Error: {error}
          </Typography>
        )}

        {portfolioData && (
          <div>
            <Typography variant="body1">
              <strong>Total Value:</strong> ${portfolioData.totalValue}
            </Typography>
            <Typography variant="body1">
              <strong>Unrealized P&L:</strong> ${portfolioData.unrealizedPnL}
            </Typography>
            <Typography variant="body1">
              <strong>Realized P&L:</strong> ${portfolioData.realizedPnL}
            </Typography>
            <Typography variant="body1">
              <strong>Timestamp:</strong> {portfolioData.timestamp}
            </Typography>
            <pre style={{ fontSize: '12px', overflow: 'auto' }}>
              {JSON.stringify(portfolioData, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default PortfolioTest;
