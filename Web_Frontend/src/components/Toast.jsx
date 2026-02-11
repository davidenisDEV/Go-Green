import React, { useEffect } from 'react';

const Toast = ({ msg, type = 'success', onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const color = type === 'error' ? 'border-red-500 text-red-500' : 'border-neon text-neon';

  return (
    <div className="cart-notification" style={{ borderColor: type === 'error' ? '#e74c3c' : '#00ff7f' }}>
      <h4 style={{ color: type === 'error' ? '#e74c3c' : '#00ff7f' }}>
        {type === 'error' ? 'Erro' : 'Sucesso'}
      </h4>
      <p>{msg}</p>
    </div>
  );
};

export default Toast;