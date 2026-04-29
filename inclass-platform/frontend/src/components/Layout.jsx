import React from 'react';
import { Outlet } from 'react-router-dom';

const Layout = () => {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', fontFamily: 'sans-serif' }}>
      {/* Üst Bar */}
      <header style={{ padding: '1rem 2rem', background: '#2c3e50', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>InClass Platform</h1>
        <nav>
          <small>Sprint 2 - Group B</small>
        </nav>
      </header>

      {/* Sayfa İçeriği */}
      <main style={{ flex: 1, padding: '2rem' }}>
        <Outlet /> {/* BURASI DEĞİŞTİ: Artık alt sayfalar burada görünecek */}
      </main>

      {/* Alt Bar */}
      <footer style={{ textAlign: 'center', padding: '1rem', background: '#ecf0f1', borderTop: '1px solid #ddd' }}>
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#7f8c8d' }}>© 2026 MEF University - SoftEng Project</p>
      </footer>
    </div>
  );
};

export default Layout;