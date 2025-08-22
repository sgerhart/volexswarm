import { useEffect, useState } from 'react';
import { useAppStore } from '../store';
import agentService from '../services/agentService';

export const useDataFetching = () => {
  const {
    setAgents,
    setPortfolio,
    updateTradingSignals,
    setActiveStrategies,
    updateMarketData,
    addNotification,
  } = useAppStore();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all data on component mount
  useEffect(() => {
    fetchAllData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchAllData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch real portfolio data from Meta Agent first
      const portfolio = await agentService.getPortfolioData();
      console.log('🔍 Fetched portfolio data:', portfolio);
      if (portfolio) {
        console.log('✅ Setting portfolio in store:', portfolio);
        setPortfolio(portfolio);
      } else {
        console.log('❌ No portfolio data received from Meta Agent');
      }

      // Fetch data from all agents in parallel
      const [
        agents,
        signals,
        strategies,
        marketData,
      ] = await Promise.all([
        agentService.checkAgentHealth(),
        agentService.getTradingSignals(),
        agentService.getActiveStrategies(),
        agentService.getMarketData(),
      ]);

      // Update store with fetched data
      if (agents) setAgents(agents);
      if (signals) updateTradingSignals(signals);
      if (strategies) setActiveStrategies(strategies);
      if (marketData) updateMarketData(marketData);

      // Show success notification
      addNotification({
        type: 'success',
        message: 'Portfolio data refreshed successfully',
        read: false,
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data';
      setError(errorMessage);
      
      addNotification({
        type: 'error',
        message: `Error fetching portfolio data: ${errorMessage}`,
        read: false,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const refreshData = () => {
    fetchAllData();
  };

  return {
    isLoading,
    error,
    refreshData,
  };
};

export default useDataFetching;
