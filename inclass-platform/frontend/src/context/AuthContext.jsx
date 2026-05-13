import React, { createContext, useContext, useMemo, useState } from 'react';
import { normalizeRole } from '../utils/helpers';

const STORAGE_KEY = 'inclass_auth_session_v1';

function readStoredSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') {
      return null;
    }

    const role = normalizeRole(parsed.role);
    const email = parsed.email ? String(parsed.email) : '';
    const password = parsed.password ? String(parsed.password) : '';

    if (!role || !email || !password) {
      return null;
    }

    return { email, password, role };
  } catch (error) {
    return null;
  }
}

function writeStoredSession(user) {
  if (!user) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredSession);

  const login = (nextUser) => {
    const payload = {
      email: String(nextUser.email || ''),
      password: String(nextUser.password || ''),
      role: normalizeRole(nextUser.role),
    };
    setUser(payload);
    writeStoredSession(payload);
  };

  const logout = () => {
    setUser(null);
    writeStoredSession(null);
  };

  const updateUser = (partial) => {
    setUser((prev) => {
      if (!prev) {
        return prev;
      }
      const next = {
        ...prev,
        ...partial,
      };
      writeStoredSession(next);
      return next;
    });
  };

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      login,
      logout,
      updateUser,
    }),
    [user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
