import unittest
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import GastoRecurrente

class TestGastoRecurrente(unittest.TestCase):
    def setUp(self):
        """Configurar el entorno de pruebas"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Limpiar después de cada prueba"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_crear_gasto_recurrente(self):
        """Probar la creación de un gasto recurrente"""
        gasto = GastoRecurrente(
            descripcion='Nómina',
            tipo_periodicidad='RECURRENTE',
            periodicidad='MENSUAL',
            meses_base='1',
            monto=5000.00
        )
        db.session.add(gasto)
        db.session.commit()

        # Verificar que se haya guardado correctamente
        self.assertIsNotNone(gasto.id)
        self.assertEqual(gasto.descripcion, 'Nómina')
        self.assertEqual(gasto.tipo_periodicidad, 'RECURRENTE')

    def test_es_mes_de_pago(self):
        """Probar la lógica de determinación de mes de pago"""
        # Gasto mensual
        gasto_mensual = GastoRecurrente(
            descripcion='Servicios Básicos',
            tipo_periodicidad='RECURRENTE',
            periodicidad='MENSUAL',
            meses_base='1'
        )
        
        # Gasto bimestral
        gasto_bimestral = GastoRecurrente(
            descripcion='Mantenimiento',
            tipo_periodicidad='RECURRENTE',
            periodicidad='BIMESTRAL',
            meses_base='1,7'
        )
        
        # Gasto fijo
        gasto_fijo = GastoRecurrente(
            descripcion='Décimo Tercero',
            tipo_periodicidad='FIJO',
            meses_base='12'
        )

        # Probar diferentes meses
        self.assertTrue(gasto_mensual.es_mes_de_pago(1, 2026))
        self.assertTrue(gasto_bimestral.es_mes_de_pago(1, 2026))
        self.assertTrue(gasto_bimestral.es_mes_de_pago(7, 2026))
        self.assertTrue(gasto_fijo.es_mes_de_pago(12, 2026))

        # Verificar meses que no son de pago
        self.assertFalse(gasto_mensual.es_mes_de_pago(2, 2026))
        self.assertFalse(gasto_bimestral.es_mes_de_pago(3, 2026))
        self.assertFalse(gasto_fijo.es_mes_de_pago(1, 2026))

    def test_crear_gastos_predeterminados(self):
        """Probar la creación de gastos predeterminados"""
        GastoRecurrente.crear_gastos_predeterminados()
        
        # Verificar que se hayan creado los gastos
        gastos = GastoRecurrente.query.all()
        self.assertTrue(len(gastos) > 0)
        
        # Verificar algunos gastos específicos
        nomina = GastoRecurrente.query.filter_by(descripcion='Nómina').first()
        self.assertIsNotNone(nomina)
        self.assertEqual(nomina.tipo_periodicidad, 'RECURRENTE')
        self.assertEqual(nomina.periodicidad, 'MENSUAL')

if __name__ == '__main__':
    unittest.main()