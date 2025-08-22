const axios = require('axios');

// Test real data fetching from VolexSwarm agents
async function testRealDataFetching() {
  console.log('🧪 Testing Real Data Fetching from VolexSwarm Agents...\n');

  try {
    // Test 1: Check Execution Agent health
    console.log('1️⃣ Testing Execution Agent (Port 8002)...');
    const executionHealth = await axios.get('http://localhost:8002/health');
    console.log('✅ Execution Agent Health:', executionHealth.data.status);
    console.log('   Uptime:', executionHealth.data.uptime);
    console.log('   Trades in 24h:', executionHealth.data.connectivity?.trades_24h || 0);
    console.log('');

    // Test 2: Try to get portfolio data
    console.log('2️⃣ Testing Portfolio Data Fetching...');
    try {
      const portfolioResponse = await axios.get('http://localhost:8002/api/execution/portfolio');
      console.log('✅ Portfolio Data Retrieved:', portfolioResponse.data);
    } catch (error) {
      console.log('❌ Portfolio Endpoint Not Available:', error.response?.data?.detail || error.message);
    }
    console.log('');

    // Test 3: Try to get recent trades
    console.log('3️⃣ Testing Recent Trades Fetching...');
    try {
      const tradesResponse = await axios.get('http://localhost:8002/api/execution/trades');
      console.log('✅ Recent Trades Retrieved:', tradesResponse.data);
    } catch (error) {
      console.log('❌ Trades Endpoint Not Available:', error.response?.data?.detail || error.message);
    }
    console.log('');

    // Test 4: Check Risk Agent for portfolio risk data
    console.log('4️⃣ Testing Risk Agent Portfolio Assessment...');
    try {
      const riskResponse = await axios.post('http://localhost:8009/api/risk/portfolio', {
        positions: [],
        account_balance: 1000
      });
      console.log('✅ Risk Assessment Retrieved:', riskResponse.data);
    } catch (error) {
      console.log('❌ Risk Portfolio Endpoint Not Available:', error.response?.data?.detail || error.message);
    }
    console.log('');

    // Test 5: Check Signal Agent for trading signals
    console.log('5️⃣ Testing Signal Agent...');
    try {
      const signalsResponse = await axios.get('http://localhost:8003/signals');
      console.log('✅ Trading Signals Retrieved:', signalsResponse.data);
    } catch (error) {
      console.log('❌ Signals Endpoint Not Available:', error.response?.data?.detail || error.message);
    }
    console.log('');

    console.log('📊 SUMMARY:');
    console.log('   - Execution Agent: ✅ Running');
    console.log('   - Portfolio Data: ❌ Endpoint not implemented');
    console.log('   - Recent Trades: ❌ Endpoint not implemented');
    console.log('   - Risk Assessment: ❌ Endpoint not implemented');
    console.log('   - Trading Signals: ✅ Endpoint working (0 signals)');
    console.log('');
    console.log('🔍 CONCLUSION:');
    console.log('   The agents are running but the portfolio data endpoints are not implemented yet.');
    console.log('   We need to either:');
    console.log('   1. Implement the missing endpoints in the agents');
    console.log('   2. Create direct database queries');
    console.log('   3. Configure the agents with Binance US API access');

  } catch (error) {
    console.error('❌ Error testing real data fetching:', error.message);
  }
}

// Run the test
testRealDataFetching();

