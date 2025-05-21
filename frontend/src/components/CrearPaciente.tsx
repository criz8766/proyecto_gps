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
      setFormData({ nombre: '', rut: '', fecha_nacimiento: '' });
    } catch (error) {
      setMensaje('Error al crear el paciente');
      console.error(error);
    }
  };

  return (
    <FormularioPaciente
      formData={formData}
      handleChange={handleChange}
      handleSubmit={handleSubmit}
      mensaje={mensaje}
    />
  );
};

export default CrearPaciente;
