import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { CartContext } from '../context/CartContext';
import { useNavigate, Link } from 'react-router-dom';
import { Search, ShoppingCart, Plus, Minus, X, Star, AlertCircle, User } from 'lucide-react';
const API_URL = "http://localhost:5000/api";

const Catalogo = () => {
  const [produtos, setProdutos] = useState([]);
  const [filtro, setFiltro] = useState('Todos');
  const [busca, setBusca] = useState('');
  
  // Modais
  const [modalOpen, setModalOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false); // Modal de Login
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [qty, setQty] = useState(1);

  const { user } = useContext(AuthContext);
  const { addToCart } = useContext(CartContext);
  const navigate = useNavigate();

  // Ordem de apresentação desejada
  const categoriasOrdem = ["Sedas", "Piteiras", "Cuias", "Fumos", "Tesouras", "Dichavadores", "Acessórios", "Outros"];
  const categoriasFiltro = ["Todos", ...categoriasOrdem];

  useEffect(() => {
    axios.get(`${API_URL}/produtos`).then(res => {
      // Ordena os produtos conforme a lista de categorias
      const ordenados = res.data.sort((a, b) => {
        const catA = a.categoria || "Outros";
        const catB = b.categoria || "Outros";
        return categoriasOrdem.indexOf(catA) - categoriasOrdem.indexOf(catB);
      });
      setProdutos(ordenados);
    });
  }, []);

  // Abre detalhes do produto
  const openProductDetails = (produto) => {
    setSelectedProduct(produto);
    setQty(1);
    setModalOpen(true);
  };

  // Tenta adicionar ao carrinho
  const handleAddToCart = () => {
    if (!user) {
      setModalOpen(false); // Fecha detalhes
      setLoginModalOpen(true); // Abre login
      return;
    }
    
    if (selectedProduct) {
      addToCart({ ...selectedProduct, qtd_solicitada: qty });
      setModalOpen(false);
      alert("Item adicionado ao carrinho! 🛒");
    }
  };

  const irParaLogin = () => {
    navigate('/login');
  };

  const irParaCadastro = () => {
    navigate('/cadastro');
  };

  // Filtros
  const produtosFiltrados = produtos.filter(p => {
    const cat = p.categoria ? p.categoria.trim() : "Outros";
    const matchCat = filtro === 'Todos' || cat === filtro;
    const matchBusca = p.nome.toLowerCase().includes(busca.toLowerCase());
    return matchCat && matchBusca;
  });

  // Separa destaques (apenas se estiver na aba Todos e sem busca)
  const destaques = produtos.filter(p => p.destaque === 1);
  const showDestaques = filtro === 'Todos' && busca === '';

  return (
    <div className="catalogo-page">
      
      {/* Header */}
      <div className="catalog-header">
        <h2>Catálogo Completo</h2>
        <div className="search-box">
          <Search size={20} color="#666"/>
          <input 
            type="text" 
            placeholder="Buscar item..." 
            value={busca} 
            onChange={e => setBusca(e.target.value)} 
          />
        </div>
      </div>

      {/* Barra de Categorias */}
      <div className="filters-bar">
        <div className="categories-list">
          {categoriasFiltro.map(cat => (
            <button 
              key={cat} 
              className={filtro === cat ? 'cat-btn active' : 'cat-btn'} 
              onClick={() => setFiltro(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="section">
        
        {/* Seção Destaques (Aparece só no início) */}
        {showDestaques && destaques.length > 0 && (
          <div className="destaques-section">
            <h3 className="section-title"><Star size={20} fill="#f1c40f" color="#f1c40f"/> Destaques da Loja</h3>
            <div className="grid-produtos">
              {destaques.map(item => (
                <ProductCard key={item.id} item={item} onClick={() => openProductDetails(item)} />
              ))}
            </div>
            <hr className="divider"/>
          </div>
        )}

        {/* Lista Geral */}
        <h3 className="section-title">{filtro === 'Todos' ? 'Todos os Produtos' : filtro}</h3>
        <div className="grid-produtos">
          {produtosFiltrados.map(item => (
            <ProductCard key={item.id} item={item} onClick={() => openProductDetails(item)} />
          ))}
          
          {produtosFiltrados.length === 0 && (
            <div className="empty-state">
              <p>Nenhum produto encontrado nesta categoria.</p>
            </div>
          )}
        </div>
      </div>

      {/* --- MODAL DETALHES DO PRODUTO --- */}
      {modalOpen && selectedProduct && (
        <div className="modal-overlay">
          <div className="modal-content product-modal">
            <button className="close-modal" onClick={() => setModalOpen(false)}><X size={24}/></button>
            
            <div className="modal-body">
              <div className="modal-img">
                 <img 
                  src={selectedProduct.imagem_url || "https://placehold.co/400x400/222/00ff7f?text=GoGreen"} 
                  alt={selectedProduct.nome} 
                />
              </div>
              
              <div className="modal-info">
                <span className="categoria-badge">{selectedProduct.categoria || 'Geral'}</span>
                <h2>{selectedProduct.nome}</h2>
                
                {selectedProduct.observacoes && (
                  <p className="prod-desc">{selectedProduct.observacoes}</p>
                )}
                
                <div className="stock-info">
                  {selectedProduct.qtd_estoque > 0 ? (
                    <span className="in-stock">Em estoque: {selectedProduct.qtd_estoque} un.</span>
                  ) : (
                    <span className="out-stock">Produto Esgotado</span>
                  )}
                </div>

                <div className="price-row">
                  <span className="price-label">Valor Unitário</span>
                  <span className="price-val">R$ {selectedProduct.preco_venda.toFixed(2)}</span>
                </div>

                {selectedProduct.qtd_estoque > 0 && (
                  <div className="actions-row">
                    <div className="qty-selector">
                      <button onClick={() => setQty(q => Math.max(1, q - 1))}><Minus size={18}/></button>
                      <span>{qty}</span>
                      <button onClick={() => setQty(q => Math.min(selectedProduct.qtd_estoque, q + 1))}><Plus size={18}/></button>
                    </div>
                    
                    <button className="btn-add-modal" onClick={handleAddToCart}>
                      ADICIONAR - R$ {(selectedProduct.preco_venda * qty).toFixed(2)}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL DE LOGIN (Bloqueio) --- */}
      {loginModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content login-modal">
            <button className="close-modal" onClick={() => setLoginModalOpen(false)}><X size={24}/></button>
            <div className="login-content">
              <User size={48} color="#00ff7f" />
              <h3>Identifique-se</h3>
              <p>Para adicionar itens ao carrinho, você precisa entrar na sua conta.</p>
              
              <div className="login-actions">
                <button className="btn-login" onClick={irParaLogin}>JÁ TENHO CONTA</button>
                <button className="btn-register" onClick={irParaCadastro}>CRIAR CONTA</button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

// Componente Cartão de Produto (Reutilizável)
const ProductCard = ({ item, onClick }) => (
  <div className="card-produto" onClick={onClick}>
    <div className="img-container">
      <img 
        src={item.imagem_url && item.imagem_url.length > 5 ? item.imagem_url : "https://placehold.co/300x300/222/00ff7f?text=GoGreen"} 
        alt={item.nome} 
      />
      {item.qtd_estoque === 0 && <span className="badge-out">Esgotado</span>}
      {item.qtd_estoque > 0 && item.qtd_estoque < 5 && <span className="badge-low">Últimos!</span>}
    </div>
    
    <div className="card-body">
      <div className="card-top">
        <span className="categoria-tag">{item.categoria || 'Geral'}</span>
        <h3>{item.nome}</h3>
      </div>
      
      <div className="card-bottom">
        <p className="preco">R$ {item.preco_venda.toFixed(2)}</p>
        <button className="btn-view" disabled={item.qtd_estoque === 0}>
          {item.qtd_estoque > 0 ? <ShoppingCart size={18}/> : <X size={18}/>}
        </button>
      </div>
    </div>
  </div>
);

export default Catalogo;