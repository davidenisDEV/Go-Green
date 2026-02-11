import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';

const Cadastro = () => {
  const [form, setForm] = useState({ nome: '', email: '', telefone: '', senha: '' });
  const navigate = useNavigate();

  const handleCadastro = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:5000/api/auth/register', form);
      alert("Conta criada com sucesso! Faça login para continuar.");
      navigate('/login');
    } catch (err) {
      alert(err.response?.data?.msg || "Erro ao criar conta.");
    }
  };

  return (
    <div className="split-screen">
      <div className="split-left" style={{backgroundImage: "url('https://images.unsplash.com/photo-1527661591475-527312dd65f5?q=80&w=1920')"}}>
        <div className="split-overlay"></div>
        <div className="split-left-content">
          <h1>Junte-se ao Clube</h1>
          <p>Crie sua conta para fazer pedidos via Delivery ou Retirada, acumular pontos e receber novidades em primeira mão.</p>
        </div>
      </div>
      
      <div className="split-right">
        <div className="form-box">
          <h2>Criar Nova Conta</h2>
          <span className="subtitle">Preencha os dados abaixo. É rápido.</span>
          
          <form onSubmit={handleCadastro}>
            <div className="input-group">
              <label>Nome Completo</label>
              <input type="text" placeholder="Seu nome" onChange={e=>setForm({...form, nome:e.target.value})} required />
            </div>

            <div className="input-group">
              <label>WhatsApp / Telefone</label>
              <input type="text" placeholder="(85) 99999-9999" onChange={e=>setForm({...form, telefone:e.target.value})} required />
            </div>

            <div className="input-group">
              <label>Email</label>
              <input type="email" placeholder="seu@email.com" onChange={e=>setForm({...form, email:e.target.value})} required />
            </div>
            
            <div className="input-group">
              <label>Senha</label>
              <input type="password" placeholder="Crie uma senha forte" onChange={e=>setForm({...form, senha:e.target.value})} required />
            </div>
            
            <button type="submit" className="btn-full">CADASTRAR</button>
          </form>
          
          <div className="form-footer">
            <p>Já possui conta? <Link to="/login">Fazer Login</Link></p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Cadastro;