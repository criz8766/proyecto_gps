from fastapi import FastAPI
from app.routes.inventario import router as inventario_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Microservicio de Inventario")

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

# Registro del router de inventario
app.include_router(inventario_router, prefix="/api/inventario")
