// frontend/src/components/FormularioPaciente.tsx
import React from 'react';
import { PacienteCreate } from '../api/pacientes'; // Asegúrate que PacienteCreate esté exportado desde api/pacientes.ts

interface Props {
  formData: PacienteCreate;
  handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: React.FormEvent) => void;
  mensaje: string;
  textoBoton?: string; // <<< Nueva prop opcional
}

const FormularioPaciente: React.FC<Props> = ({ formData, handleChange, handleSubmit, mensaje, textoBoton = "Crear Paciente" }) => { // <<< Valor por defecto
  return (
    // No es necesario envolverlo en crear-paciente-container si se usa en un modal
    // pero puedes mantenerlo si el modal no provee su propio contenedor estilizado.
    // Para este ejemplo, asumimos que el modal maneja el contenedor.
    <form onSubmit={handleSubmit}>
      {/* Si no estás en un modal, podrías querer el título aquí */}
      {/* <h2>{textoBoton}</h2> */}
      <div className="input-group">
        <label className="input-label">Nombre:</label>
        <input type="text" name="nombre" value={formData.nombre} onChange={handleChange} className="input-field" required />
      </div>
      <div className="input-group">
        <label className="input-label">RUT:</label>
        <input type="text" name="rut" value={formData.rut} onChange={handleChange} className="input-field" required />
      </div>
      <div className="input-group">
        <label className="input-label">Fecha de Nacimiento:</label>
        <input type="date" name="fecha_nacimiento" value={formData.fecha_nacimiento} onChange={handleChange} className="input-field" required />
      </div>
      <button type="submit" className="submit-button">{textoBoton}</button> {/* <<< Usar la prop textoBoton */}
      {/* El mensaje se maneja fuera para el modal de edición, pero se mantiene para el de creación */}
      {mensaje && <p className="mensaje">{mensaje}</p>} 
    </form>
  );
};

export default FormularioPaciente;