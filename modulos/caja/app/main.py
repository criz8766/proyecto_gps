from fastapi import FastAPI
from routes.caja import router as caja_router
from database import init_db
from fastapi.middleware.cors import CORSMiddleware

# Inicializar la base de datos al arrancar
init_db()

app = FastAPI(title="Microservicio de Caja")

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

# Registro del router de caja
app.include_router(caja_router, prefix="/api/caja")

@app.get("/")
def read_root():
    return {"message": "Microservicio de Caja funcionando correctamente"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "caja"}