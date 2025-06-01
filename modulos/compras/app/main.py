from fastapi import FastAPI
from routes.compras import router as compras_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Microservicio de Compras")

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

# Registro del router de compras
app.include_router(compras_router, prefix="/api/compras")