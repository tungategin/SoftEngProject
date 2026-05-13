import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import { instructorLogin, studentLogin } from '../api/authApi';
import { useAuth } from '../context/AuthContext';
import { formatValidationErrors, mapErrorCodeToMessage } from '../utils/helpers';

const ROLE_OPTIONS = [
  { value: 'student', label: 'Student' },
  { value: 'instructor', label: 'Instructor' },
];

export default function LoginPage() {
  const [role, setRole] = useState('student');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate();
  const { login } = useAuth();

  const heading = useMemo(
    () => (role === 'instructor' ? 'Instructor Login' : 'Student Login'),
    [role],
  );

  const onSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsLoading(true);

    const apiCall = role === 'instructor' ? instructorLogin : studentLogin;
    const result = await apiCall(email.trim(), password);

    if (!result.ok) {
      if (result.error === 'validation_error') {
        setError(formatValidationErrors(result.validation));
      } else {
        const base = mapErrorCodeToMessage(result.error);
        const detail = result.detail ? ` (${result.detail})` : '';
        setError(base + detail);
      }
      setIsLoading(false);
      return;
    }

    login({ email: email.trim(), password, role });
    navigate(role === 'instructor' ? '/app/instructor' : '/app/student', { replace: true });
    setIsLoading(false);
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <span className="eyebrow">InClass Platform</span>
          <h1>{heading}</h1>
          <p>Use your platform credentials and continue with your role-specific workspace.</p>
        </div>

        <div className="role-toggle" role="tablist" aria-label="Role selector">
          {ROLE_OPTIONS.map((option) => (
            <button
              type="button"
              key={option.value}
              className={role === option.value ? 'role-btn role-btn-active' : 'role-btn'}
              onClick={() => setRole(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="form-grid">
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="user@example.com"
              required
              autoComplete="username"
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </label>

          {error ? <div className="alert alert-error">{error}</div> : null}

          <Button type="submit" loading={isLoading} block>
            Sign In
          </Button>
        </form>
      </div>
    </div>
  );
}
