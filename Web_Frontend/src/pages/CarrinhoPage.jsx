import React, { useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { CartContext } from '../context/CartContext';
import { AuthContext } from '../context/AuthContext'; // Importe AuthContext
import { Trash2, Copy, CheckCircle, ArrowLeft, Banknote, QrCode } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom'; // Importe useNavigate

const API_URL = "http://localhost:5000/api";

const CarrinhoPage = () => {
  const { cart, removeFromCart, clearCart, total } = useContext(CartContext);
  const { user } = useContext(AuthContext); // Pega o usuário logado
  const [step, setStep] = useState(1);
  const [cliente, setCliente] = useState({ nome: '', contato: '' });
  const [metodoPagamento, setMetodoPagamento] = useState('Pix'); 
  const navigate = useNavigate();
  
  const CHAVE_PIX = "daviddenis0112@gmail.com"; 

  // Preenche dados automaticamente se o usuário estiver logado
  useEffect(() => {
    if (user) {
      setCliente({ nome: user.nome || '', contato: user.telefone || '' });
    }
  }, [user]);

  const finalizarPedido = async () => {
    if (!user) {
      alert("Faça login para finalizar o pedido.");
      navigate('/login');
      return;
    }

    if (!cliente.nome || !cliente.contato) {
      alert("Por favor, confirme seus dados.");
      return;
    }

    try {
      await axios.post(`${API_URL}/pedidos/novo`, {
        cliente,
        carrinho: cart,
        total,
        pagamento: metodoPagamento
      }, {
        // Envia o token se necessário pelo backend, ou user_id
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setStep(2);
      clearCart();
    } catch (error) {
      console.error(error);
      alert("Erro ao enviar pedido. Verifique sua conexão.");
    }
  };

  const copiarPix = () => {
    navigator.clipboard.writeText(CHAVE_PIX);
    alert("Chave PIX copiada!");
  };

  // TELA DE SUCESSO
  if (step === 2) return (
    <div className="section" style={{textAlign: 'center', padding: '100px 20px'}}>
      <CheckCircle size={100} color="#2ecc71" style={{margin: '0 auto 20px'}} />
      <h2 style={{color: '#2ecc71'}}>Pedido Recebido!</h2>
      <p style={{fontSize: '1.2rem', color: '#ccc'}}>Seu pedido está <b>PENDENTE</b> de aprovação.</p>
      
      <div style={{background: '#1e1e1e', padding: 30, borderRadius: 15, margin: '40px auto', maxWidth: 600, border: '1px solid #333'}}>
        <h3 style={{color: 'white', marginBottom: 20}}>O que fazer agora?</h3>
        
        {metodoPagamento === 'Pix' ? (
          <ol style={{textAlign: 'left', lineHeight: '2', color: '#aaa'}}>
            <li>Realize o PIX de <b>R$ {total.toFixed(2)}</b>.</li>
            <li>Envie o comprovante no nosso WhatsApp (Botão abaixo).</li>
            <li>Aguarde a confirmação para retirar/receber.</li>
          </ol>
        ) : (
          <ol style={{textAlign: 'left', lineHeight: '2', color: '#aaa'}}>
            <li>Dirija-se ao nosso endereço para retirada.</li>
            <li>Informe seu nome: <b>{cliente.nome}</b> no balcão.</li>
            <li>Realize o pagamento em Dinheiro ou Pix na hora.</li>
          </ol>
        )}
      </div>
      
      <a 
        href="https://wa.me/5585996699921" target="_blank" rel="noreferrer"
        className="btn-full" 
        style={{display: 'inline-block', width: 'auto', padding: '15px 40px', textDecoration: 'none'}}
      >
        Falar no WhatsApp
      </a>
      <br/><br/>
      <Link to="/" style={{color: '#888'}}>Voltar para a Loja</Link>
    </div>
  );

  // TELA DO CARRINHO
  return (
    <div className="cart-page-container">
      <h2 style={{borderBottom: '2px solid #2ecc71', display: 'inline-block', marginBottom: 40, fontSize: '2rem', color: '#00ff7f'}}>Seu Carrinho</h2>
      
      {cart.length === 0 ? (
        <div style={{textAlign: 'center', padding: 50}}>
          <ShoppingBag size={64} color="#333" style={{marginBottom: 20}}/>
          <p style={{fontSize: '1.5rem', color: 'gray'}}>Seu carrinho está vazio.</p>
          <Link to="/catalogo" className="btn-full" style={{display: 'inline-block', marginTop: 20, width: 'auto', padding: '10px 30px', textDecoration: 'none'}}>Ver Produtos</Link>
        </div>
      ) : (
        <div className="checkout-grid">
          
          {/* LISTA DE ITENS */}
          <div className="cart-list">
            {cart.map(item => (
              <div key={item.id} className="cart-item-row">
                <div className="cart-item-info">
                  <img src={item.imagem_url} alt={item.nome} />
                  <div className="cart-item-details">
                    <h4>{item.nome}</h4>
                    <p>{item.qtd}x R$ {item.preco_venda.toFixed(2)}</p>
                  </div>
                </div>
                <div className="cart-actions">
                    <span className="cart-price">R$ {(item.preco_venda * item.qtd).toFixed(2)}</span>
                    <button onClick={() => removeFromCart(item.id)} className="btn-remove"><Trash2 size={18}/></button>
                </div>
              </div>
            ))}
            <Link to="/catalogo" style={{display: 'flex', alignItems: 'center', gap: 10, marginTop: 20, color: '#aaa'}}><ArrowLeft size={18}/> Adicionar mais itens</Link>
          </div>

          {/* CHECKOUT BOX */}
          <div className="checkout-box">
            <h3 style={{marginTop: 0, color: 'white'}}>Resumo do Pedido</h3>
            <div className="total-row" style={{display: 'flex', justifyContent: 'space-between', fontSize: '1.5rem', fontWeight: 'bold', margin: '20px 0', color: '#00ff7f'}}>
              <span>Total:</span>
              <span>R$ {total.toFixed(2)}</span>
            </div>

            <hr className="divider" style={{borderColor: '#333', margin: '20px 0'}} />

            <h4 style={{color: 'white', marginBottom: 10}}>Seus Dados</h4>
            <input type="text" placeholder="Nome Completo" className="input-group input" style={{width: '100%', marginBottom: 10}} value={cliente.nome} onChange={e => setCliente({...cliente, nome:e.target.value})} />
            <input type="text" placeholder="WhatsApp / Contato" className="input-group input" style={{width: '100%', marginBottom: 20}} value={cliente.contato} onChange={e => setCliente({...cliente, contato:e.target.value})} />

            <h4 style={{color: 'white', marginBottom: 10}}>Forma de Pagamento</h4>
            <div className="payment-options" style={{display: 'flex', flexDirection: 'column', gap: 10}}>
              <label className={`pay-option ${metodoPagamento === 'Pix' ? 'active' : ''}`} style={{display: 'flex', alignItems: 'center', gap: 10, padding: 15, background: '#2a2a2a', borderRadius: 8, border: metodoPagamento === 'Pix' ? '1px solid #00ff7f' : '1px solid #444', cursor: 'pointer'}}>
                <input type="radio" name="pgto" value="Pix" checked={metodoPagamento === 'Pix'} onChange={() => setMetodoPagamento('Pix')} />
                <QrCode size={20} color="white"/> <span style={{color:'white'}}>Pix Online (Agilizar)</span>
              </label>
              
              <label className={`pay-option ${metodoPagamento === 'Dinheiro' ? 'active' : ''}`} style={{display: 'flex', alignItems: 'center', gap: 10, padding: 15, background: '#2a2a2a', borderRadius: 8, border: metodoPagamento === 'Dinheiro' ? '1px solid #00ff7f' : '1px solid #444', cursor: 'pointer'}}>
                <input type="radio" name="pgto" value="Dinheiro" checked={metodoPagamento === 'Dinheiro'} onChange={() => setMetodoPagamento('Dinheiro')} />
                <Banknote size={20} color="white"/> <span style={{color:'white'}}>Pagar na Retirada</span>
              </label>
            </div>

            {metodoPagamento === 'Pix' && (
              <div className="pix-area-box" style={{background: '#333', padding: 15, borderRadius: 5, border: '1px dashed #00ff7f', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 20}}>
                <span style={{color: 'white', fontSize: '0.9rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px'}}>Chave: {CHAVE_PIX}</span>
                <button onClick={copiarPix} style={{background: 'none', border: 'none', color: '#00ff7f', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5}}><Copy size={16}/> Copiar</button>
              </div>
            )}

            <button 
              className="btn-full" 
              style={{marginTop: 20}}
              disabled={!cliente.nome || !cliente.contato}
              onClick={finalizarPedido}
            >
              CONFIRMAR PEDIDO
            </button>
          </div>

        </div>
      )}
    </div>
  );
};

export default CarrinhoPage;