from fastapi import FastAPI
from routes.stock import router as stock_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Microservicio de Stock")

# Configuración de CORS
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock_router, prefix="/api/stock")
