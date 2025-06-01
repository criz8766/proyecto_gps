from fastapi import FastAPI
from routes.usuarios import router as usuarios_router
from fastapi.middleware.cors import CORSMiddleware
from database import init_db

app = FastAPI(title="Microservicio de Gestión de Usuarios")

# Configuración CORS
origins = [
    "http://localhost:3000",  # Tu frontend en Next.js (o React)
    # Puedes agregar otros orígenes aquí si los necesitas
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar base de datos al arrancar la aplicación
@app.on_event("startup")
async def startup_event():
    init_db()

# Registro del router de usuarios
app.include_router(usuarios_router, prefix="/api/usuarios")

@app.get("/")
async def root():
    return {"message": "Microservicio de Gestión de Usuarios - Sistema de Farmacia Comunal"}