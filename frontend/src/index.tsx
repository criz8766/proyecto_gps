import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';  // asegúrate que esto apunta a tu App.tsx que usa <Pacientes />

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
