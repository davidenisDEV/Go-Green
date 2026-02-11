import React, { useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [remember, setRemember] = useState(false); // Novo Estado
  
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      // Envia a flag 'remember' para o backend definir a validade do token
      const res = await axios.post('http://localhost:5000/api/auth/login', { 
        email, 
        senha, 
        remember 
      });
      
      login(res.data.token, res.data.user);
      navigate('/'); 
    } catch (err) {
      alert("Email ou senha incorretos.");
    }
  };

  return (
    <div className="split-screen">
      <div className="split-left">
        <div className="split-overlay"></div>
        <div className="split-left-content">
          <h1>GO GREEN 🌿</h1>
          <p>Acesse sua conta para gerenciar seus pedidos, ver seu histórico e aproveitar ofertas exclusivas da nossa comunidade.</p>
        </div>
      </div>
      
      <div className="split-right">
        <div className="form-box">
          <h2>Bem-vindo de volta!</h2>
          <span className="subtitle">Insira seus dados para entrar.</span>
          
          <form onSubmit={handleLogin}>
            <div className="input-group">
              <label>Email</label>
              <input 
                type="email" 
                placeholder="exemplo@email.com" 
                value={email} 
                onChange={e=>setEmail(e.target.value)} 
                required 
              />
            </div>
            
            <div className="input-group">
              <label>Senha</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={senha} 
                onChange={e=>setSenha(e.target.value)} 
                required 
              />
            </div>

            {/* CHECKBOX MANTER CONECTADO */}
            <div className="checkbox-group">
              <input 
                type="checkbox" 
                id="remember" 
                checked={remember} 
                onChange={e => setRemember(e.target.checked)} 
              />
              <label htmlFor="remember">Manter-me conectado</label>
            </div>
            
            <button type="submit" className="btn-full">ENTRAR</button>
          </form>
          
          <div className="form-footer">
            <p>Ainda não tem conta? <Link to="/cadastro">Cadastre-se</Link></p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;