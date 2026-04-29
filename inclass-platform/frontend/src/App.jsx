import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage.jsx';
import Layout from './components/Layout.jsx';
import InstructorDashboard from './pages/InstructorDashboard.jsx';
import StudentActivityPage from './pages/StudentActivityPage.jsx';
import { AuthProvider } from './context/AuthContext.jsx';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Ana giriş sayfası */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Kök dizine geleni login'e yönlendir */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* Dashboard ve uygulama içi sayfalar (Layout sarmallı) */}
          <Route path="/app" element={<Layout />}>
            <Route path="instructor" element={<InstructorDashboard />} />
            <Route path="student" element={<StudentActivityPage />} />
          </Route>

          {/* Tanımsız yollar için güvenlik önlemi */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;