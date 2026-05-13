import React from 'react';
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import { AuthProvider, useAuth } from './context/AuthContext';
import InstructorDashboard from './pages/InstructorDashboard';
import LoginPage from './pages/LoginPage';
import StudentActivityPage from './pages/StudentActivityPage';

function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function RoleRoute({ requiredRole, children }) {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (user.role !== requiredRole) {
    const fallbackPath = user.role === 'instructor' ? '/app/instructor' : '/app/student';
    return <Navigate to={fallbackPath} replace />;
  }
  return children;
}

function LoginRoute() {
  const { user } = useAuth();
  if (user) {
    const path = user.role === 'instructor' ? '/app/instructor' : '/app/student';
    return <Navigate to={path} replace />;
  }
  return <LoginPage />;
}

function HomeRedirect() {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <Navigate to={user.role === 'instructor' ? '/app/instructor' : '/app/student'} replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<LoginRoute />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<Layout />}>
          <Route index element={<HomeRedirect />} />
          <Route
            path="student"
            element={(
              <RoleRoute requiredRole="student">
                <StudentActivityPage />
              </RoleRoute>
            )}
          />
          <Route
            path="instructor"
            element={(
              <RoleRoute requiredRole="instructor">
                <InstructorDashboard />
              </RoleRoute>
            )}
          />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
