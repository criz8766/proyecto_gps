from fastapi import FastAPI
from routes.informe import router as informes_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Microservicio de Informes")

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

# Registro del router de informes
app.include_router(informes_router, prefix="/api/informes")
