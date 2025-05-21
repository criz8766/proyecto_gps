import React from 'react';
import { PacienteCreate } from '../api/pacientes';

interface Props {
  formData: PacienteCreate;
  handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: React.FormEvent) => void;
  mensaje: string;
}

const FormularioPaciente: React.FC<Props> = ({ formData, handleChange, handleSubmit, mensaje }) => {
  return (
    <div className="crear-paciente-container">
      <h2 className="crear-paciente-title">Crear Paciente</h2>
      <form onSubmit={handleSubmit}>
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
        <button type="submit" className="submit-button">Crear Paciente</button>
      </form>
      {mensaje && <p className="mensaje">{mensaje}</p>}
    </div>
  );
};

export default FormularioPaciente;
