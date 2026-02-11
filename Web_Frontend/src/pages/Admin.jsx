import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Package, Edit, Trash2, Upload, Save, X, Search, Image as ImageIcon } from 'lucide-react';
const API_URL = "http://localhost:5000/api";

const Admin = () => {
  const { user, token, logout } = useContext(AuthContext); // Adicionei logout aqui
  const navigate = useNavigate();

  const [produtos, setProdutos] = useState([]);
  const [busca, setBusca] = useState('');
  const [editingProd, setEditingProd] = useState(null);
  const [loading, setLoading] = useState(true);
  const [previewImg, setPreviewImg] = useState(null);

  // Form Data
  const [form, setForm] = useState({
    nome: '', preco_venda: '', qtd_estoque: '', categoria: 'Geral', observacoes: '', destaque: 0, imagem_url: ''
  });

  useEffect(() => {
    if (!token) { navigate('/login'); return; }
    // Verifica se tem role admin (opcional, pois o backend barra também)
    if (user && user.role !== 'admin') {
        alert("Acesso restrito.");
        navigate('/');
    }
    carregarProdutos();
  }, [token, user]);

  const carregarProdutos = async () => {
    try {
      const res = await axios.get(`${API_URL}/produtos`);
      setProdutos(res.data);
    } catch (error) { console.error("Erro produtos:", error); } 
    finally { setLoading(false); }
  };

  const handleEdit = (prod) => {
    setEditingProd(prod);
    setForm({
      nome: prod.nome,
      preco_venda: prod.preco_venda,
      qtd_estoque: prod.qtd_estoque,
      categoria: prod.categoria || 'Geral',
      observacoes: prod.observacoes || '',
      destaque: prod.destaque || 0,
      imagem_url: prod.imagem_url || ''
    });
    setPreviewImg(prod.imagem_url);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCancel = () => {
    setEditingProd(null);
    setPreviewImg(null);
    setForm({ nome: '', preco_venda: '', qtd_estoque: '', categoria: 'Geral', observacoes: '', destaque: 0, imagem_url: '' });
  };

  // --- UPLOAD DE IMAGEM (Blindado) ---
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Preview local imediato
    setPreviewImg(URL.createObjectURL(file));

    const formData = new FormData();
    formData.append('file', file);
    formData.append('tipo', 'produto');
    
    try {
      const res = await axios.post(`${API_URL}/upload`, formData, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' }
      });
      // Salva a URL retornada no estado do form
      setForm(prev => ({ ...prev, imagem_url: res.data.url }));
    } catch (error) {
      alert("Erro no upload. Tente uma imagem menor ou JPG/PNG.");
      console.error(error);
    }
  };

  // --- SALVAR NO BANCO (Tratativa 422) ---
  const handleSave = async () => {
    if (!editingProd) return;

    // Conversão e Sanitização dos Dados
    const preco = parseFloat(form.preco_venda);
    const estoque = parseInt(form.qtd_estoque);

    if (isNaN(preco) || isNaN(estoque)) {
      return alert("Por favor, preencha Preço e Estoque com números válidos.");
    }

    const payload = {
      nome: form.nome,
      preco_venda: preco,
      qtd_estoque: estoque,
      categoria: form.categoria,
      observacoes: form.observacoes,
      destaque: form.destaque ? 1 : 0,
      // Usa a nova imagem se houver, senão mantém a antiga
      imagem_url: form.imagem_url || editingProd.imagem_url
    };

    try {
      await axios.put(`${API_URL}/produtos/${editingProd.id}`, payload, {
        headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json' 
        }
      });

      alert("✅ Produto salvo com sucesso!");
      handleCancel();
      carregarProdutos();
    } catch (error) {
      console.error("Erro ao salvar:", error.response);
      if (error.response?.status === 422 || error.response?.status === 401) {
          alert("Sessão expirada ou inválida. Faça login novamente.");
          logout();
          navigate('/login');
      } else {
          alert("Erro ao salvar produto. Verifique o console.");
      }
    }
  };

  const produtosFiltrados = produtos.filter(p => p.nome.toLowerCase().includes(busca.toLowerCase()));

  if (loading) return <div className="admin-container" style={{color:'white', padding:100, textAlign:'center'}}>Carregando...</div>;

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h1>Painel Administrativo</h1>
        <p>Gerencie o estoque e catálogo.</p>
      </div>

      <div className="admin-content">
        {/* LISTA */}
        <div className="admin-list-section">
          <div className="admin-search-bar">
            <Search size={20} color="#666"/>
            <input type="text" placeholder="Buscar..." value={busca} onChange={e => setBusca(e.target.value)} />
          </div>
          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Foto</th>
                  <th>Produto</th>
                  <th>Preço</th>
                  <th>Qtd</th>
                  <th>Ação</th>
                </tr>
              </thead>
              <tbody>
                {produtosFiltrados.map(p => (
                  <tr key={p.id} className={editingProd?.id === p.id ? 'active-row' : ''}>
                    <td><img src={p.imagem_url || "https://placehold.co/50/222/00ff7f"} className="thumb-small" alt="prod"/></td>
                    <td>{p.nome} {p.destaque === 1 && <span className="tag-destaque">★</span>}</td>
                    <td>R$ {p.preco_venda.toFixed(2)}</td>
                    <td style={{color: p.qtd_estoque < 5 ? '#e74c3c' : 'white'}}>{p.qtd_estoque}</td>
                    <td><button className="btn-icon-edit" onClick={() => handleEdit(p)}><Edit size={18}/></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* FORMULÁRIO */}
        <div className="admin-form-section">
          {editingProd ? (
            <div className="admin-form-box fade-in">
              <div className="form-header">
                <h3>Editando Produto #{editingProd.id}</h3>
                <button onClick={handleCancel}><X size={20}/></button>
              </div>
              
              <div className="img-upload-area">
                <img src={previewImg || "https://placehold.co/300x200/222/00ff7f"} alt="Preview" />
                <label htmlFor="upload-btn" className="btn-upload-custom">
                  <Upload size={16}/> Trocar Foto
                </label>
                <input id="upload-btn" type="file" onChange={handleFileChange} hidden accept="image/*"/>
              </div>

              <div className="form-grid">
                <div className="input-group">
                  <label>Nome</label>
                  <input type="text" value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} />
                </div>
                <div className="row-2">
                  <div className="input-group">
                    <label>Preço (R$)</label>
                    <input type="number" step="0.01" value={form.preco_venda} onChange={e => setForm({...form, preco_venda: e.target.value})} />
                  </div>
                  <div className="input-group">
                    <label>Estoque</label>
                    <input type="number" value={form.qtd_estoque} onChange={e => setForm({...form, qtd_estoque: e.target.value})} />
                  </div>
                </div>
                <div className="input-group">
                  <label>Categoria</label>
                  <select value={form.categoria} onChange={e => setForm({...form, categoria: e.target.value})}>
                    <option value="Geral">Geral</option>
                    <option value="Sedas">Sedas</option>
                    <option value="Piteiras">Piteiras</option>
                    <option value="Cuias">Cuias</option>
                    <option value="Fumos">Fumos</option>
                    <option value="Tesouras">Tesouras</option>
                    <option value="Dichavadores">Dichavadores</option>
                    <option value="Acessórios">Acessórios</option>
                    <option value="Outros">Outros</option>
                  </select>
                </div>
                <div className="input-group">
                  <label>Descrição</label>
                  <textarea rows="3" value={form.observacoes} onChange={e => setForm({...form, observacoes: e.target.value})}></textarea>
                </div>
                <div className="checkbox-group">
                  <input type="checkbox" id="chk" checked={form.destaque === 1} onChange={e => setForm({...form, destaque: e.target.checked ? 1 : 0})} />
                  <label htmlFor="chk">Destaque na Home</label>
                </div>
                <button className="btn-save-full" onClick={handleSave}><Save size={20}/> SALVAR</button>
              </div>
            </div>
          ) : (
            <div className="empty-selection"><Package size={48}/><p>Selecione um item para editar.</p></div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Admin;