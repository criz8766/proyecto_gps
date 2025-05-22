// frontend/src/App.tsx
import React from 'react';
import CrearPaciente from './components/CrearPaciente';
import ListarPacientes from './components/ListarPacientes'; // <<< IMPORTAR
import './App.css'; // Puedes mantener o quitar esto si no lo usas

function App() {
  return (
    <div className="App"> {/* Puedes usar la clase App o una nueva si prefieres */}
      <header className="App-header"> {/* Opcional: si quieres mantener la cabecera */}
        <h1>Gestión de Pacientes</h1>
      </header>
      <main>
        <CrearPaciente />
        <hr className="separador" /> {/* Separador visual opcional */}
        <ListarPacientes />
      </main>
    </div>
  );
}

export default App;