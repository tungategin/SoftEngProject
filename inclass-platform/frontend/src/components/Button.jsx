import React from 'react';

export default function Button({
  children,
  type = 'button',
  onClick,
  disabled = false,
  loading = false,
  variant = 'primary',
  size = 'md',
  block = false,
  className = '',
}) {
  const cls = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    block ? 'btn-block' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button type={type} onClick={onClick} disabled={disabled || loading} className={cls}>
      {loading ? 'Please wait...' : children}
    </button>
  );
}
