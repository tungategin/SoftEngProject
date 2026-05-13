import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import Button from './Button';
import { useAuth } from '../context/AuthContext';

function NavItem({ to, label }) {
  return (
    <NavLink to={to} className={({ isActive }) => (isActive ? 'nav-item nav-item-active' : 'nav-item')}>
      {label}
    </NavLink>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-wrap">
          <div className="brand-mark">IC</div>
          <div>
            <h1 className="brand-title">InClass Platform</h1>
            <p className="brand-subtitle">Interactive Learning</p>
          </div>
        </div>

        <div className="session-card">
          <p className="session-email">{user ? user.email : ''}</p>
          <span className="role-chip">{user && user.role === 'instructor' ? 'Instructor' : 'Student'}</span>
        </div>

        <nav className="sidebar-nav">
          {user && user.role === 'instructor' ? (
            <NavItem to="/app/instructor" label="Instructor Workspace" />
          ) : (
            <NavItem to="/app/student" label="Student Workspace" />
          )}
        </nav>

        <div className="sidebar-footer">
          <Button variant="ghost" block onClick={handleLogout}>Logout</Button>
        </div>
      </aside>

      <section className="content-shell">
        <header className="topbar">
          <div>
            <h2>{user && user.role === 'instructor' ? 'Instructor Console' : 'Student Tutoring Area'}</h2>
            <p>Backend-integrated frontend aligned with API contract.</p>
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
      </section>
    </div>
  );
}
