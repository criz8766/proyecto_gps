from fastapi import FastAPI
from app.routes.pacientes import router as pacientes_router
from fastapi.middleware.cors import CORSMiddleware # <--- 1. IMPORTA ESTO

app = FastAPI(title="Microservicio de Pacientes")

# --- 2. AÑADE ESTA SECCIÓN DE CONFIGURACIÓN DE CORS ---
origins = [
    "http://localhost:3000",  # El origen de tu frontend React
    # Si tuvieras otros orígenes (ej. una app móvil, otro frontend) los añadirías aquí
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Lista de orígenes permitidos
    allow_credentials=True,    # Permite cookies, cabeceras de autorización, etc. (importante si usas tokens)
    allow_methods=["*"],       # Permite todos los métodos HTTP (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],       # Permite todas las cabeceras HTTP
)
# --- FIN DE LA SECCIÓN DE CORS ---

app.include_router(pacientes_router, prefix="/api/pacientes")