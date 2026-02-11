import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { 
  MapPin, Clock, Mail, MessageCircle, 
  ChevronLeft, ChevronRight, ShoppingBag, 
  Banknote, Truck, ShieldCheck, Star, Instagram, X, CreditCard
} from 'lucide-react';
const API_URL = "http://localhost:5000/api";

const Home = () => {
  const [destaques, setDestaques] = useState([]);
  const [novidades, setNovidades] = useState([]);
  const [indexCar, setIndexCar] = useState(0);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API_URL}/produtos`);
        const prods = res.data;
        
        // Destaques (para Carrossel e Seção 1)
        const d = prods.filter(p => p.destaque === 1);
        setDestaques(d.length > 0 ? d : prods.slice(0, 5));

        // Novidades (Últimos itens adicionados)
        const n = prods.slice(-4).reverse(); 
        setNovidades(n);
      } catch (error) {
        console.error("Erro ao carregar home:", error);
      }
    };
    fetchData();
  }, []);

  // Timer Carrossel
  useEffect(() => {
    const t = setInterval(() => {
      setIndexCar(prev => (prev + 1) % (destaques.length || 1));
    }, 5000);
    return () => clearInterval(t);
  }, [destaques]);

  const nextSlide = () => setIndexCar((prev) => (prev + 1) % (destaques.length || 1));
  const prevSlide = () => setIndexCar((prev) => (prev - 1 + (destaques.length || 1)) % (destaques.length || 1));

  // Mensagem pronta para o WhatsApp
  const msgZap = encodeURIComponent("Opa, gostaria de ver o catálogo da GoGreen");
  const linkZap = `https://wa.me/5585996699921?text=${msgZap}`;

  return (
    <div className="home-container">
      
      {/* 1. CARROSSEL (Hero) */}
      <section className="hero-carousel-section">
        {destaques.length > 0 ? (
          <div className="home-carousel-container">
            <button className="carousel-btn prev" onClick={prevSlide}><ChevronLeft size={40}/></button>
            <button className="carousel-btn next" onClick={nextSlide}><ChevronRight size={40}/></button>

            {destaques.map((item, idx) => (
              <div key={item.id} className="carousel-slide" 
                   style={{
                     backgroundImage: `url(${item.imagem_url || 'https://placehold.co/1200x600/111/00ff7f?text=GoGreen'})`, 
                     opacity: idx === indexCar ? 1 : 0,
                     pointerEvents: idx === indexCar ? 'auto' : 'none'
                   }}>
                <div className="carousel-overlay">
                  <div className="carousel-content">
                    <h1>{item.nome}</h1>
                    <p className="hero-price">R$ {item.preco_venda.toFixed(2)}</p>
                    <Link to="/catalogo" className="btn-hero">COMPRAR AGORA</Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{display:'flex', alignItems:'center', justifyContent:'center', height:'100%', color:'gray'}}>
            Carregando Destaques...
          </div>
        )}
      </section>

      {/* 2. BENEFÍCIOS (Barra Intermediária) */}
      <section className="benefits-section">
        <div className="benefits-grid">
          
          {/* Card Pagamento (Abre Modal) */}
          <div className="benefit-card" onClick={() => setShowPaymentModal(true)} style={{cursor: 'pointer'}}>
            <Banknote size={40} color="#00ff7f" />
            <h3>Formas de Pagamento</h3>
            <p>Pix, Dinheiro e Cartão. Clique para ver detalhes.</p>
          </div>

          <div className="benefit-card">
            <Truck size={40} color="#00ff7f" />
            <h3>Entrega Expressa</h3>
            <p>Envio via Uber Flash para toda Fortaleza e região.</p>
          </div>

          {/* Card WhatsApp (Link Direto) */}
          <a href={linkZap} target="_blank" rel="noopener noreferrer" className="benefit-card" style={{textDecoration:'none'}}>
            <MessageCircle size={40} color="#00ff7f" />
            <h3>Atendimento VIP</h3>
            <p>Dúvidas? Fale direto com a gente no WhatsApp.</p>
          </a>

          <div className="benefit-card">
            <ShieldCheck size={40} color="#00ff7f" />
            <h3>Garantia GoGreen</h3>
            <p>Produtos originais selecionados a dedo.</p>
          </div>
        </div>
      </section>

      {/* 3. PRODUTOS DESTAQUES (Vitrine A) */}
      <section className="showcase-section dark-bg">
        <div className="section-header-left">
          <Star size={24} color="#f1c40f" />
          <h2>Destaques da Loja</h2>
        </div>
        <div className="showcase-grid">
          {destaques.slice(0, 4).map(item => (
            <Link to="/catalogo" key={item.id} className="mini-product-card">
              <img src={item.imagem_url || "https://placehold.co/200x200/222/00ff7f"} alt={item.nome} />
              <div className="mini-info">
                <h4>{item.nome}</h4>
                <span>R$ {item.preco_venda.toFixed(2)}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* 4. PRODUTOS NOVIDADES (Vitrine B) */}
      <section className="showcase-section light-bg">
        <div className="section-header-left">
          <ShoppingBag size={24} color="#00ff7f" />
          <h2>Novidades</h2>
        </div>
        <div className="showcase-grid">
          {novidades.map(item => (
            <Link to="/catalogo" key={item.id} className="mini-product-card">
              <div className="badge-new">NOVO</div>
              <img src={item.imagem_url || "https://placehold.co/200x200/222/00ff7f"} alt={item.nome} />
              <div className="mini-info">
                <h4>{item.nome}</h4>
                <span>R$ {item.preco_venda.toFixed(2)}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* 5. LOCALIZAÇÃO E CONTATO (Profissional) */}
      <section className="section" id="contato">
        <div className="section-header">
          <h2>Localização & Contato</h2>
          <p>Venha conhecer nosso espaço ou peça sem sair de casa.</p>
        </div>

        <div className="contact-grid">
          <div className="map-frame">
            <iframe 
              src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3981.353385732688!2d-38.51357602414732!3d-3.7328905432098656!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x7c748625902094d%3A0xc3f9823f950212a4!2sR.%20Bar%C3%A3o%20de%20Aracati%2C%20609%20-%20Meireles%2C%20Fortaleza%20-%20CE%2C%2060115-080!5e0!3m2!1spt-BR!2sbr!4v1700000000000!5m2!1spt-BR!2sbr" 
              width="100%" height="100%" style={{border:0}} allowFullScreen="" loading="lazy">
            </iframe>
          </div>

          <div className="info-box">
            <div className="info-item">
              <MapPin size={24} color="#2ecc71" style={{minWidth: 24}}/>
              <div>
                <h4>Ponto de Retirada (GoGreen & Fuzuê)</h4>
                <p>R. Barão de Aracati, 609 - Meireles, Fortaleza - CE</p>
              </div>
            </div>

            <div className="info-item">
              <Clock size={24} color="#2ecc71" style={{minWidth: 24}}/>
              <div>
                <h4>Horário de Funcionamento</h4>
                <p>Quarta a Domingo: <strong>18:00 às 00:00</strong></p>
                <p style={{fontSize:'0.8rem', color:'#888'}}>Entregas e retirada no balcão.</p>
              </div>
            </div>

            <div className="info-item">
              <MessageCircle size={24} color="#2ecc71" style={{minWidth: 24}}/>
              <div>
                <h4>Central de Atendimento</h4>
                <a href={linkZap} target="_blank" className="link-zap" style={{marginTop:5, display:'inline-block'}}>
                   Falar no WhatsApp (85) 99669-9921
                </a>
              </div>
            </div>

            <div className="info-item">
              <Instagram size={24} color="#2ecc71" style={{minWidth: 24}}/>
              <div>
                <h4>Nossas Redes</h4>
                <div style={{display:'flex', gap:'15px', marginTop:5, flexWrap:'wrap'}}>
                  <a href="https://instagram.com/GoGreenHeadshop" target="_blank" style={{color:'#fff', fontWeight:'bold', borderBottom:'1px solid #2ecc71'}}>@GoGreenHeadshop</a>
                  <a href="https://instagram.com/Fuzue.bar" target="_blank" style={{color:'#fff', fontWeight:'bold', borderBottom:'1px solid #f39c12'}}>@Fuzue.bar</a>
                </div>
              </div>
            </div>

            <div className="info-item">
              <Mail size={24} color="#2ecc71" style={{minWidth: 24}}/>
              <div>
                <h4>Email Corporativo</h4>
                <a href="mailto:cooltivocomp@gmail.com" style={{color:'#ccc'}}>cooltivocomp@gmail.com</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- MODAL DE PAGAMENTO --- */}
      {showPaymentModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="close-modal" onClick={() => setShowPaymentModal(false)}><X size={24}/></button>
            
            <div style={{textAlign: 'center'}}>
              <CreditCard size={48} color="#00ff7f" style={{marginBottom: 15}}/>
              <h3 style={{color:'white', fontSize:'1.5rem', margin:'0 0 20px 0'}}>Formas de Pagamento</h3>
              
              <div style={{textAlign:'left', color:'#ccc', lineHeight:'1.8', background:'#121212', padding: 20, borderRadius: 10, border:'1px solid #333'}}>
                <p>✅ <strong>Pix</strong> (Instantâneo e sem taxas)</p>
                <p>✅ <strong>Dinheiro</strong> (Pagamento na retirada)</p>
                <hr style={{borderColor:'#333', margin:'10px 0'}}/>
                <p>💳 <strong>Cartão de Débito</strong></p>
                <p>💳 <strong>Cartão de Crédito</strong></p>
                
                <div style={{marginTop: 15, padding: 10, background:'#2c2c2c', borderRadius: 5, borderLeft: '4px solid #f1c40f'}}>
                  <small style={{color:'#fff'}}>
                    ⚠️ <strong>Atenção:</strong> Para pagamentos no cartão (crédito ou débito), é cobrado o acréscimo da taxa da maquineta.
                  </small>
                </div>
              </div>

              <button className="btn-confirm-add" style={{marginTop: 20}} onClick={() => setShowPaymentModal(false)}>
                ENTENDIDO
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Home;