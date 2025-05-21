export interface Paciente {
  id: number;
  nombre: string;
  rut: string;
  fecha_nacimiento: string;
  // Otros campos según tu backend
}

const BASE_URL = 'http://localhost:8000/api';

export interface Paciente {
  id: number;
  nombre: string;
  rut: string;
  fecha_nacimiento: string;
}

export interface PacienteCreate {
  nombre: string;
  rut: string;
  fecha_nacimiento: string;
}

export async function crearPaciente(paciente: PacienteCreate): Promise<Paciente> {
  const response = await fetch(`${BASE_URL}/pacientes/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(paciente),
  });

  if (!response.ok) {
    throw new Error('Error al crear paciente');
  }

  return await response.json();
}

