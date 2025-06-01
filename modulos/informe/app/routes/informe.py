from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import date

from app.models import (
    ReporteFacturasResponse,
    ReporteConsumosResponse,
    ProductoSinMovimientoResponse
)
from app.database import get_database
from app.security import require_permission
from app.kafka_producer import enviar_evento

router = APIRouter()

@router.get("/facturas", response_model=ReporteFacturasResponse)
async def reporte_facturas(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    user=Depends(require_permission("ver:informes")),
    db=Depends(get_database)
):
    if fecha_fin < fecha_inicio:
        raise HTTPException(status_code=400, detail="fecha_fin debe ser mayor o igual a fecha_inicio")

    facturas = await db.obtener_facturas(fecha_inicio, fecha_fin)
    monto_total = sum(f.monto_total for f in facturas)
    total_facturas = len(facturas)

    response = ReporteFacturasResponse(
        total_facturas=total_facturas,
        monto_total=monto_total,
        facturas=facturas
    )

    enviar_evento("informes-events", {
        "accion": "REPORTE_FACTURAS_GENERADO",
        "usuario": user.username,
        "fecha_inicio": str(fecha_inicio),
        "fecha_fin": str(fecha_fin),
        "total_facturas": total_facturas,
        "monto_total": monto_total
    })

    return response

# Aquí el resto de endpoints similares...
