from fastapi import FastAPI
from routes.beneficiarios import router as beneficiarios_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Microservicio de Beneficiarios")

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

# Registro del router de beneficiarios
app.include_router(beneficiarios_router, prefix="/api/beneficiarios")