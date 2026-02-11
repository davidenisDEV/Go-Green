import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { User, Wallet, Heart, LogOut, Camera, Plus, Trash2, Edit2, Save, Loader } from 'lucide-react';
const API_URL = "http://localhost:5000/api";

const Perfil = () => {
  const { token, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const [dados, setDados] = useState(null);
  const [favoritos, setFavoritos] = useState([]);
  const [activeTab, setActiveTab] = useState('dados'); 
  const [loading, setLoading] = useState(true);
  
  // Estados Edição
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [depositoValor, setDepositoValor] = useState('');

  useEffect(() => {
    // Se não tiver token, tchau
    if (!token) { 
      logout(); 
      navigate('/login'); 
      return; 
    }
    carregarTudo();
  }, [token]);

  const carregarTudo = async () => {
    setLoading(true);
    try {
      const [resPerfil, resFav] = await Promise.all([
        axios.get(`${API_URL}/minha-conta`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/favoritos`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setDados(resPerfil.data);
      setFormData(resPerfil.data);
      setFavoritos(resFav.data);
    } catch (error) {
      console.error("Erro ao carregar perfil:", error);
      // CORREÇÃO: Se der 401 (Não autorizado) ou 422 (Token antigo/inválido), desloga
      if (error.response && (error.response.status === 401 || error.response.status === 422)) {
        logout();
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  // ... (Funções handleSaveProfile, handlePhotoUpload, etc. mantêm-se iguais) ...
  const handleSaveProfile = async () => {
    try {
      setIsEditing(false);
      setDados(formData);
      alert("Dados salvos visualmente!");
    } catch (e) { alert("Erro ao salvar."); }
  };

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const data = new FormData();
    data.append('file', file);
    data.append('tipo', 'perfil');
    try {
      const res = await axios.post(`${API_URL}/upload`, data, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' }
      });
      await axios.put(`${API_URL}/minha-conta/update`, { foto_perfil: res.data.url }, { headers: { Authorization: `Bearer ${token}` } });
      setDados(prev => ({ ...prev, foto_perfil: res.data.url }));
    } catch (e) { alert("Erro ao enviar foto."); }
  };

  const toggleNewsletter = async () => {
    if (!dados) return;
    const novo = dados.newsletter === 1 ? 0 : 1;
    try {
      await axios.put(`${API_URL}/minha-conta/update`, { newsletter: novo }, { headers: { Authorization: `Bearer ${token}` } });
      setDados({ ...dados, newsletter: novo });
    } catch (e) { alert("Erro."); }
  };
  
  const handleDeposito = async () => {
     const val = parseFloat(depositoValor);
     if (!val || val <= 0) return alert("Valor inválido");
     try {
       await axios.post(`${API_URL}/carteira/depositar`, { valor: val }, { headers: { Authorization: `Bearer ${token}` } });
       alert("Depósito realizado!"); setDepositoValor(''); carregarTudo();
     } catch (e) { alert("Erro."); }
  };

  const removerFavorito = async (id) => {
      try {
          await axios.delete(`${API_URL}/favoritos`, { headers: {Authorization: `Bearer ${token}`}, data: {produto_id: id}});
          setFavoritos(prev => prev.filter(p => p.id !== id));
      } catch(e) { alert("Erro"); }
  };

  // LOADING E ERRO VISUAL
  if (loading) return (
    <div className="section" style={{display:'flex', justifyContent:'center', alignItems:'center', height:'60vh'}}>
      <Loader className="animate-spin" color="#00ff7f" size={48} />
    </div>
  );

  // Se parou de carregar mas não tem dados (ex: erro de rede que não é 401/422)
  if (!dados) return (
    <div className="section" style={{textAlign:'center', padding:50, color:'white'}}>
      <h2>Não foi possível carregar os dados.</h2>
      <button onClick={() => window.location.reload()} className="btn-full" style={{width:'auto', padding:'10px 30px'}}>Tentar Novamente</button>
    </div>
  );

  return (
    <div className="section perfil-page">
      <div className="perfil-sidebar">
        <div className="profile-pic-container">
          <img src={dados.foto_perfil || "https://placehold.co/500x500/1e1e1e/00ff7f?text=USER"} alt="Perfil" className="profile-pic"/>
          <label htmlFor="upload-foto" className="btn-edit-photo"><Camera size={16}/></label>
          <input type="file" id="upload-foto" style={{display:'none'}} onChange={handlePhotoUpload} accept="image/*"/>
        </div>
        
        <h3>{dados.nome ? dados.nome.split(' ')[0] : 'Usuário'}</h3>
        
        <nav className="perfil-nav">
          <button className={activeTab === 'dados' ? 'active' : ''} onClick={() => setActiveTab('dados')}><User size={18}/> Meus Dados</button>
          <button className={activeTab === 'carteira' ? 'active' : ''} onClick={() => setActiveTab('carteira')}><Wallet size={18}/> Carteira</button>
          <button className={activeTab === 'favoritos' ? 'active' : ''} onClick={() => setActiveTab('favoritos')}><Heart size={18}/> Favoritos</button>
          <button onClick={() => { logout(); navigate('/login'); }} className="logout-btn"><LogOut size={18}/> Sair</button>
        </nav>
      </div>

      <div className="perfil-content">
        {activeTab === 'dados' && (
          <div className="tab-pane fade-in">
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 20}}>
                <h2 style={{color:'#00ff7f', margin:0}}>Informações Pessoais</h2>
                {!isEditing ? (
                    <button className="btn-edit-profile" onClick={() => setIsEditing(true)}>
                        <Edit2 size={16} style={{marginRight:5}}/> Editar
                    </button>
                ) : (
                    <button className="btn-save-profile" onClick={handleSaveProfile}>
                        <Save size={16} style={{marginRight:5}}/> Salvar
                    </button>
                )}
            </div>
            
            <div className="info-grid-perfil">
              <div className="info-field">
                <label>Nome</label>
                <input 
                    type="text" 
                    value={isEditing ? (formData.nome || '') : (dados.nome || '')} 
                    onChange={e => setFormData({...formData, nome: e.target.value})}
                    readOnly={!isEditing} 
                    className={isEditing ? 'editable' : ''}
                />
              </div>
              <div className="info-field">
                <label>Email</label>
                <input type="text" value={dados.email || ''} readOnly disabled style={{opacity: 0.7}}/>
              </div>
              <div className="info-field">
                <label>Telefone</label>
                <input 
                    type="text" 
                    value={isEditing ? (formData.telefone || '') : (dados.telefone || '')} 
                    onChange={e => setFormData({...formData, telefone: e.target.value})}
                    readOnly={!isEditing}
                    className={isEditing ? 'editable' : ''}
                />
              </div>
            </div>

            <div className="newsletter-box">
              <input type="checkbox" checked={dados.newsletter === 1} onChange={toggleNewsletter} />
              <div><h4>Newsletter</h4><p>Desejo receber promoções e novidades por email.</p></div>
            </div>
          </div>
        )}
        
        {activeTab === 'carteira' && (
             <div className="tab-pane fade-in">
                 <h2 style={{color:'#00ff7f'}}>Carteira Digital</h2>
                 <div className="wallet-card"><span>Saldo Atual</span><h1>R$ {dados.saldo ? dados.saldo.toFixed(2) : '0.00'}</h1></div>
                 <div className="deposit-area">
                    <h3>Adicionar Saldo</h3>
                    <div className="input-row">
                        <input type="number" placeholder="R$ 0,00" value={depositoValor} onChange={e => setDepositoValor(e.target.value)} />
                        <button onClick={handleDeposito}><Plus size={18}/> Depositar</button>
                    </div>
                 </div>
                 <div className="history-area">
                    <h3>Histórico</h3>
                    <ul>
                        {dados.transacoes && dados.transacoes.map(t => (
                            <li key={t.id}>
                                <span>{t.tipo ? t.tipo.toUpperCase() : 'MOVIMENTO'}</span>
                                <span style={{color: t.tipo === 'deposito' ? '#00ff7f' : 'white'}}>
                                {t.tipo === 'deposito' ? '+' : '-'} R$ {t.valor ? t.valor.toFixed(2) : '0.00'}
                                </span>
                            </li>
                        ))}
                    </ul>
                 </div>
             </div>
        )}
        
        {activeTab === 'favoritos' && (
             <div className="tab-pane fade-in">
                 <h2 style={{color:'#00ff7f'}}>Meus Favoritos</h2>
                 <div className="fav-grid">
                    {favoritos.map(prod => (
                        <div key={prod.id} className="fav-card">
                            <img src={prod.imagem_url || "https://placehold.co/300/222/00ff7f"} alt={prod.nome} />
                            <div className="fav-info">
                                <h4>{prod.nome}</h4>
                                <p>R$ {prod.preco_venda ? prod.preco_venda.toFixed(2) : '0.00'}</p>
                                <button className="btn-remove-fav" onClick={() => removerFavorito(prod.id)}><Trash2 size={16}/> Remover</button>
                            </div>
                        </div>
                    ))}
                    {favoritos.length === 0 && <p>Nenhum favorito.</p>}
                 </div>
             </div>
        )}
      </div>
    </div>
  );
};

export default Perfil;