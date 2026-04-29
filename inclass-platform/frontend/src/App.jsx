import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage.jsx'; // .jsx ekledik
import Layout from './components/Layout.jsx';   // .jsx ekledik
import { AuthProvider } from './context/AuthContext.jsx'; // .jsx ekledik

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/app" element={<Layout />}>
             {/* İç sayfalar buraya gelecek */}
          </Route>
          {/* Tanımsız yollar için fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;