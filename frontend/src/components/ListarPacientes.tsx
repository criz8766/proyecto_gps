// frontend/src/components/ListarPacientes.tsx
import React, { useState, useEffect } from 'react';
import { listarPacientes, Paciente, PacienteCreate, actualizarPaciente, eliminarPaciente } from '../api/pacientes';
import FormularioPaciente from './FormularioPaciente'; // Reutilizaremos este formulario
import './ListarPacientes.css';

const ListarPacientes: React.FC = () => {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [mensaje, setMensaje] = useState('');
  const [cargando, setCargando] = useState(true);
  const [pacienteAEditar, setPacienteAEditar] = useState<Paciente | null>(null);
  const [mostrarFormularioEdicion, setMostrarFormularioEdicion] = useState(false);
  const [formDataEdicion, setFormDataEdicion] = useState<PacienteCreate>({
    nombre: '',
    rut: '',
    fecha_nacimiento: '',
  });

  const cargarPacientes = async () => {
    try {
      setCargando(true);
      const data = await listarPacientes();
      setPacientes(data);
      setMensaje('');
    } catch (error) {
      console.error(error);
      setMensaje(error instanceof Error ? `Error al cargar pacientes: ${error.message}` : 'Error desconocido al cargar pacientes');
      setPacientes([]);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarPacientes();
  }, []);

  const handleEliminar = async (id: number) => {
    if (window.confirm('¿Estás seguro de que deseas eliminar este paciente?')) {
      try {
        await eliminarPaciente(id);
        setMensaje('Paciente eliminado exitosamente.');
        cargarPacientes(); // Recargar la lista
      } catch (error) {
        console.error(error);
        setMensaje(error instanceof Error ? `Error al eliminar paciente: ${error.message}` : 'Error desconocido al eliminar paciente');
      }
    }
  };

  const abrirFormularioEdicion = (paciente: Paciente) => {
    setPacienteAEditar(paciente);
    setFormDataEdicion({
      nombre: paciente.nombre,
      rut: paciente.rut,
      fecha_nacimiento: paciente.fecha_nacimiento,
    });
    setMostrarFormularioEdicion(true);
    setMensaje(''); // Limpiar mensajes anteriores
  };

  const cerrarFormularioEdicion = () => {
    setMostrarFormularioEdicion(false);
    setPacienteAEditar(null);
  };

  const handleChangeEdicion = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormDataEdicion({
      ...formDataEdicion,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmitEdicion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pacienteAEditar) return;

    try {
      await actualizarPaciente(pacienteAEditar.id, formDataEdicion);
      setMensaje('Paciente actualizado exitosamente.');
      cerrarFormularioEdicion();
      cargarPacientes(); // Recargar la lista
    } catch (error) {
      console.error(error);
      setMensaje(error instanceof Error ? `Error al actualizar paciente: ${error.message}` : 'Error desconocido al actualizar paciente');
    }
  };


  if (cargando) {
    return <p className="listar-pacientes-mensaje">Cargando pacientes...</p>;
  }

  return (
    <div className="listar-pacientes-container">
      <h2 className="listar-pacientes-title">Lista de Pacientes</h2>
      {mensaje && <p className={`listar-pacientes-mensaje ${mensaje.includes('Error') ? 'error' : 'success'}`}>{mensaje}</p>}
      
      {mostrarFormularioEdicion && pacienteAEditar && (
        <div className="modal-edicion">
          <div className="modal-contenido">
            <span className="cerrar-modal" onClick={cerrarFormularioEdicion}>&times;</span>
            <h3>Editando Paciente: {pacienteAEditar.nombre} (ID: {pacienteAEditar.id})</h3>
            <FormularioPaciente
              formData={formDataEdicion}
              handleChange={handleChangeEdicion}
              handleSubmit={handleSubmitEdicion}
              mensaje="" // El mensaje principal se maneja fuera del formulario
              // Puedes cambiar el texto del botón si lo deseas, o añadir una prop al FormularioPaciente
            />
          </div>
        </div>
      )}

      {pacientes.length === 0 && !mensaje.includes('Error') && !cargando && (
        <p className="listar-pacientes-mensaje">No hay pacientes registrados.</p>
      )}
      {pacientes.length > 0 && (
        <table className="pacientes-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>RUT</th>
              <th>Fecha de Nacimiento</th>
              <th>Acciones</th> {/* Nueva columna */}
            </tr>
          </thead>
          <tbody>
            {pacientes.map((paciente) => (
                <tr key={paciente.id}>
                <td>{paciente.id}</td>
                <td>{paciente.nombre}</td>
                <td>{paciente.rut}</td>
                <td>{paciente.fecha_nacimiento}</td>
                <td>
                    <button className="editar-button" onClick={() => abrirFormularioEdicion(paciente)}>Editar</button>
                    <button className="eliminar-button" onClick={() => handleEliminar(paciente.id)}>Eliminar</button>
                </td>
                </tr>
            ))}
            </tbody>
        </table>
      )}
    </div>
  );
};

export default ListarPacientes;