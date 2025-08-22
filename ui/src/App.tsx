import React from 'react';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useAppStore } from './store';
import { getTheme } from './theme';
import Layout from './components/common/Layout';
import Dashboard from './components/dashboard/Dashboard';
import Trading from './components/trading/Trading';
import Intelligence from './components/intelligence/Intelligence';
import './App.css';

function App() {
  const { ui } = useAppStore();
  const theme = getTheme(ui.theme);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/trading" element={<Trading />} />
              <Route path="/intelligence" element={<Intelligence />} />
            </Routes>
          </Layout>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
