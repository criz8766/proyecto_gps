// frontend/src/components/CrearPaciente.tsx
import React, { useState } from 'react';
import { crearPaciente, PacienteCreate } from '../api/pacientes';
import FormularioPaciente from './FormularioPaciente';
import './CrearPaciente.css';

const CrearPaciente: React.FC = () => {
  const [formData, setFormData] = useState<PacienteCreate>({
    nombre: '',
    rut: '',
    fecha_nacimiento: '',
  });

  const [mensaje, setMensaje] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const paciente = await crearPaciente(formData);
      setMensaje(`Paciente creado con ID: ${paciente.id}`);
      setFormData({ nombre: '', rut: '', fecha_nacimiento: '' }); // Limpiar formulario
    } catch (error) {
      setMensaje(error instanceof Error ? `Error al crear el paciente: ${error.message}` : 'Error desconocido al crear el paciente');
      console.error(error);
    }
  };

  return (
    <div className="crear-paciente-container"> {/* Contenedor principal para la sección de creación */}
      <h2 className="crear-paciente-title">Crear Paciente</h2>
      <FormularioPaciente
        formData={formData}
        handleChange={handleChange}
        handleSubmit={handleSubmit}
        mensaje={mensaje}
        textoBoton="Crear Paciente" // <<< Especificar texto del botón
      />
    </div>
  );
};

export default CrearPaciente;