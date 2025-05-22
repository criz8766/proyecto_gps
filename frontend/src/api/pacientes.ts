// frontend/src/api/pacientes.ts
export interface Paciente {
  id: number;
  nombre: string;
  rut: string;
  fecha_nacimiento: string;
}

const BASE_URL = 'http://localhost:8000/api';

export interface PacienteCreate { // Este se usará también para la data de actualización
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
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Error al crear paciente');
  }

  return await response.json();
}

export async function listarPacientes(): Promise<Paciente[]> {
  const response = await fetch(`${BASE_URL}/pacientes/`);
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Error al listar pacientes');
  }
  return await response.json();
}

// <<< NUEVA FUNCIÓN PARA ACTUALIZAR >>>
export async function actualizarPaciente(id: number, pacienteData: PacienteCreate): Promise<Paciente> {
  const response = await fetch(`${BASE_URL}/pacientes/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(pacienteData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `Error al actualizar paciente con ID ${id}`);
  }
  return await response.json();
}

// <<< NUEVA FUNCIÓN PARA ELIMINAR >>>
export async function eliminarPaciente(id: number): Promise<void> {
  const response = await fetch(`${BASE_URL}/pacientes/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok && response.status !== 204) { // 204 es No Content, lo que esperamos en un DELETE exitoso
    const errorData = await response.json().catch(() => ({ detail: 'Error desconocido al eliminar paciente' }));
    throw new Error(errorData.detail || `Error al eliminar paciente con ID ${id}`);
  }
  // No se retorna response.json() porque para DELETE con 204 no hay cuerpo
}