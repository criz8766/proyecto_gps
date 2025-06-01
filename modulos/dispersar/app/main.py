from fastapi import FastAPI
from routes.dispersar import (router as dispersar_router)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Microservicio de Dispersión")

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

# Registro del router de dispersión
app.include_router(dispersar_router, prefix="/api/dispersar")