from datetime import datetime, timedelta
from sqlalchemy import func, case
from app.extensions import db
from app.models import Movimiento

def grafico_ingresos_egresos_6_meses():
    inicio = datetime.now() - timedelta(days=180)

    resultados = (
        db.session.query(
            func.date_trunc('month', Movimiento.fecha_pago).label('mes'),
            func.sum(
                case(
                    (Movimiento.tipo == 'INGRESO', Movimiento.monto),
                    else_=0
                )
            ).label('ingresos'),
            func.sum(
                case(
                    (Movimiento.tipo == 'EGRESO', Movimiento.monto),
                    else_=0
                )
            ).label('egresos')
        )
        .filter(
            Movimiento.fecha_pago.isnot(None),
            Movimiento.fecha_pago >= inicio,
            Movimiento.estado == 'PAGADO',
            Movimiento.es_transferencia.is_(False)
        )
        .group_by('mes')
        .order_by('mes')
        .all()
    )

    labels = [r.mes.strftime('%b %Y') for r in resultados]
    ingresos = [float(r.ingresos or 0) for r in resultados]
    egresos = [float(r.egresos or 0) for r in resultados]

    return {
        "labels": labels,
        "ingresos": ingresos,
        "egresos": egresos
    }
