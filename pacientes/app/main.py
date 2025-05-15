from fastapi import FastAPI
from app.routes.pacientes import router as pacientes_router

app = FastAPI(title="Microservicio de Pacientes")

app.include_router(pacientes_router, prefix="/api/pacientes")

