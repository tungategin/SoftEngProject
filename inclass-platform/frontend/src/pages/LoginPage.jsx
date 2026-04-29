import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { loginUser } from '../api/authService'; // API bağlantısını ekledik
import Button from '../components/Button'; // Kendi butonumuzu ekledik

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false); // Yüklenme durumu
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // E-posta üzerinden rolü tahmin et (Backend tam hazır olana kadar yardımcı olur)
    const role = email.includes('instructor') ? 'instructor' : 'student';

    try {
      // Backend'e (localhost:8000) gerçek isteği gönderiyoruz
      const data = await loginUser(email, password, role); 
      
      // Backend services.py şu an sadece { "ok": true } döndüğü için bunu kontrol ediyoruz
      if (data && data.ok) {
        setUser({ email, role }); // Kullanıcıyı Context'e kaydet
        
        // Rol bazlı yönlendirme
        if (role === 'instructor') {
          navigate('/app/instructor');
        } else {
          navigate('/app/student');
        }
      } else {
        alert("Giriş bilgileri hatalı!");
      }
    } catch (error) {
      console.error("Login hatası:", error);
      alert("Sunucuya bağlanılamadı. Lütfen backend'in 8000 portunda çalıştığından emin ol.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      maxWidth: '400px', 
      margin: '80px auto', 
      padding: '30px', 
      border: '1px solid #eee', 
      borderRadius: '12px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      backgroundColor: '#fff',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h2 style={{ textAlign: 'center', color: '#2c3e50', marginBottom: '20px' }}>InClass Giriş</h2>
      
      <form onSubmit={handleLogin}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>E-posta</label>
          <input 
            type="email" 
            placeholder="örnek@mef.edu.tr"
            value={email} 
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ccc', boxSizing: 'border-box' }}
            required 
          />
        </div>

        <div style={{ marginBottom: '25px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Şifre</label>
          <input 
            type="password" 
            placeholder="••••••••"
            value={password} 
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ccc', boxSizing: 'border-box' }}
            required 
          />
        </div>

        {/* Kendi Button bileşenimizi kullandık */}
        <Button 
          type="submit" 
          disabled={loading}
          style={{ width: '100%', backgroundColor: loading ? '#ccc' : '#3498db' }}
        >
          {loading ? "Giriş Yapılıyor..." : "Giriş Yap"}
        </Button>
      </form>
    </div>
  );
}