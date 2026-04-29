import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage.jsx';
import Layout from './components/Layout.jsx';
import InstructorDashboard from './pages/InstructorDashboard.jsx';
import StudentActivityPage from './pages/StudentActivityPage.jsx';
import { AuthProvider, useAuth } from './context/AuthContext.jsx'; // useAuth eklendi

// Giriş yapılmamışsa login'e, rol yanlışsa ana sayfaya şutlayan koruma bileşeni
const ProtectedRoute = ({ children, requiredRole }) => {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Ana giriş sayfası */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Kök dizine geleni login'e yönlendir */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* Dashboard ve uygulama içi sayfalar (Layout ve Koruma sarmallı) */}
          <Route path="/app" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route 
              path="instructor" 
              element={
                <ProtectedRoute requiredRole="instructor">
                  <InstructorDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="student" 
              element={
                <ProtectedRoute requiredRole="student">
                  <StudentActivityPage />
                </ProtectedRoute>
              } 
            />
          </Route>

          {/* Tanımsız yollar için güvenlik önlemi */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;