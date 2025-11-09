import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import ThemeGenerator from './pages/ThemeGenerator';
import TrendGenerator from './pages/TrendGenerator';
import ManualEditor from './pages/ManualEditor';
import PromptSettings from './pages/PromptSettings';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // ローカルストレージから認証状態を確認
    const auth = localStorage.getItem('isAuthenticated');
    if (auth === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
    localStorage.setItem('isAuthenticated', 'true');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('session_id');  // セッションIDも削除
  };

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" />
            ) : (
              <Login onLogin={handleLogin} />
            )
          } 
        />
        {isAuthenticated ? (
          <>
            <Route 
              path="/dashboard" 
              element={<Dashboard onLogout={handleLogout} />} 
            />
            <Route 
              path="/settings" 
              element={<Settings />} 
            />
            <Route 
              path="/theme-generator" 
              element={<ThemeGenerator />} 
            />
            <Route 
              path="/trend-generator" 
              element={<TrendGenerator />} 
            />
            <Route 
              path="/manual-editor" 
              element={<ManualEditor />} 
            />
            <Route 
              path="/prompt-settings" 
              element={<PromptSettings />} 
            />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </>
        ) : (
          <Route path="*" element={<Navigate to="/login" />} />
        )}
      </Routes>
    </Router>
  );
}

export default App;

