import React, { createContext, useState, useEffect } from 'react';

export const CartContext = createContext();

export const CartProvider = ({ children }) => {
  // Carrega do localStorage para não perder o carrinho se der F5
  const [cart, setCart] = useState(() => {
    const saved = localStorage.getItem('gogreen_cart');
    return saved ? JSON.parse(saved) : [];
  });

  // Salva no localStorage sempre que o carrinho mudar
  useEffect(() => {
    localStorage.setItem('gogreen_cart', JSON.stringify(cart));
  }, [cart]);

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      // Se o produto veio com uma qtd_solicitada (do prompt), usamos ela. Senão é 1.
      const qtdToAdd = product.qtd_solicitada || 1;

      if (existing) {
        return prev.map(item => item.id === product.id ? { ...item, qtd: item.qtd + qtdToAdd } : item);
      }
      return [...prev, { ...product, qtd: qtdToAdd }];
    });
  };

  const removeFromCart = (id) => {
    setCart(prev => prev.filter(item => item.id !== id));
  };

  const clearCart = () => setCart([]);

  const total = cart.reduce((acc, item) => acc + (item.preco_venda * item.qtd), 0);

  return (
    <CartContext.Provider value={{ cart, addToCart, removeFromCart, clearCart, total }}>
      {children}
    </CartContext.Provider>
  );
};