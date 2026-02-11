import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { CartContext } from '../context/CartContext';
import { ShoppingBag, LogOut, User } from 'lucide-react';

// IMPORTANTE: Importe sua imagem aqui
import logoImg from '../assets/logo-gogreen.png'; 

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const { cart } = useContext(CartContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <nav className="navbar">
      {/* 1. LOGO IMAGEM CLICÁVEL */}
      <Link to="/" onClick={scrollToTop} className="logo-container">
        <img src={logoImg} alt="Go Green Logo" className="logo-img" />
      </Link>
      
      <div className="menu">
        <Link to="/">Início</Link>
        <Link to="/catalogo">Produtos</Link>
        
        {/* Ícone de Carrinho */}
        <Link to="/carrinho" className="btn-cart-container">
          <ShoppingBag size={24} color={cart.length > 0 ? "#00ff7f" : "white"}/>
          {cart.length > 0 && <span className="cart-badge">{cart.length}</span>}
        </Link>

        {/* Área do Usuário */}
        {user ? (
          <>
            <Link to="/minha-conta" className="btn-user" style={{color:'var(--verde)', fontWeight:'bold'}}>
              <span style={{display:'flex', alignItems:'center', gap:5}}>
                 <User size={18}/> {user.nome.split(' ')[0]}
              </span>
            </Link>
            <button onClick={handleLogout} style={{background:'none', border:'none', cursor:'pointer'}} title="Sair">
              <LogOut size={20} color="#e74c3c"/>
            </button>
          </>
        ) : (
          <Link to="/login" style={{border:'1px solid var(--neon)', padding:'8px 15px', borderRadius:'5px', color:'var(--neon)'}}>
            Entrar
          </Link>
        )}
      </div>
    </nav>
  );
};

export default Navbar;