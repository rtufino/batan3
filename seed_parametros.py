"""
Script para poblar la tabla de parámetros con valores iniciales del sistema.
Ejecutar con: python seed_parametros.py
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from app import create_app, db
from app.models import Parametro
from datetime import datetime

def seed_parametros():
    """Crea los parámetros iniciales del sistema"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Iniciando seed de parámetros del sistema...")
        
        # ==================== PARÁMETROS GENERALES ====================
        print("\n📋 1. Creando parámetros generales...")
        
        Parametro.set_parametro(
            'nombre_edificio', 
            'Edificio Batan 3', 
            'TEXT', 
            'Nombre del edificio o condominio',
            'GENERAL'
        )
        
        Parametro.set_parametro(
            'direccion', 
            'Av. Eloy Alfaro y Batan, Quito - Ecuador', 
            'TEXT', 
            'Dirección física del edificio',
            'GENERAL'
        )
        
        Parametro.set_parametro(
            'ruc_edificio', 
            '1234567890001', 
            'TEXT', 
            'RUC del condominio',
            'GENERAL'
        )
        
        # ==================== PARÁMETROS DE NOTIFICACIONES ====================
        print("📧 2. Creando parámetros de notificaciones...")
        
        Parametro.set_parametro(
            'enviar_emails_automaticos', 
            True, 
            'BOOLEAN', 
            'Activar envío automático de emails de notificación',
            'NOTIFICACIONES'
        )
        
        Parametro.set_parametro(
            'dias_antes_vencimiento', 
            5, 
            'NUMBER', 
            'Días antes del vencimiento para enviar recordatorio de pago',
            'NOTIFICACIONES'
        )
        
        Parametro.set_parametro(
            'enviar_recordatorio_mora', 
            True, 
            'BOOLEAN', 
            'Enviar recordatorios automáticos a morosos',
            'NOTIFICACIONES'
        )
        
        Parametro.set_parametro(
            'frecuencia_recordatorio_mora_dias', 
            15, 
            'NUMBER', 
            'Cada cuántos días enviar recordatorio a morosos',
            'NOTIFICACIONES'
        )
        
        # ==================== PARÁMETROS FINANCIEROS ====================
        print("💰 3. Creando parámetros financieros...")
        
        Parametro.set_parametro(
            'dia_vencimiento_expensas', 
            10, 
            'NUMBER', 
            'Día del mes en que vencen las expensas ordinarias',
            'FINANZAS'
        )
        
        Parametro.set_parametro(
            'interes_mora_mensual', 
            2.5, 
            'NUMBER', 
            'Porcentaje de interés por mora mensual (%)',
            'FINANZAS'
        )
        
        Parametro.set_parametro(
            'aplicar_interes_mora', 
            False, 
            'BOOLEAN', 
            'Aplicar automáticamente interés por mora',
            'FINANZAS'
        )
        
        Parametro.set_parametro(
            'cuenta_predeterminada_ingresos', 
            'Banco Pichincha', 
            'TEXT', 
            'Cuenta predeterminada para registrar ingresos',
            'FINANZAS'
        )
        
        Parametro.set_parametro(
            'cuenta_predeterminada_egresos', 
            'Banco Pichincha', 
            'TEXT', 
            'Cuenta predeterminada para registrar egresos',
            'FINANZAS'
        )
        
        Parametro.set_parametro(
            'moneda', 
            'USD', 
            'TEXT', 
            'Moneda utilizada en el sistema',
            'FINANZAS'
        )
        
        # ==================== PARÁMETROS DE CONTACTO ====================
        print("📞 4. Creando parámetros de contacto...")
        
        Parametro.set_parametro(
            'telefono_administracion', 
            '0987654321', 
            'TEXT', 
            'Teléfono de contacto de la administración',
            'CONTACTO'
        )
        
        Parametro.set_parametro(
            'email_administracion', 
            'admin@batan3.com', 
            'TEXT', 
            'Email de contacto de la administración',
            'CONTACTO'
        )
        
        Parametro.set_parametro(
            'whatsapp_administracion', 
            '593987654321', 
            'TEXT', 
            'WhatsApp de la administración (con código de país)',
            'CONTACTO'
        )
        
        Parametro.set_parametro(
            'horario_atencion', 
            'Lunes a Viernes: 9:00 AM - 5:00 PM', 
            'TEXT', 
            'Horario de atención al público',
            'CONTACTO'
        )
        
        # ==================== PARÁMETROS DE SISTEMA ====================
        print("⚙️  5. Creando parámetros de sistema...")
        
        Parametro.set_parametro(
            'version_sistema', 
            '1.0.0', 
            'TEXT', 
            'Versión actual del sistema',
            'SISTEMA'
        )
        
        Parametro.set_parametro(
            'fecha_instalacion', 
            datetime.now().strftime('%Y-%m-%d'), 
            'DATE', 
            'Fecha de instalación del sistema',
            'SISTEMA'
        )
        
        Parametro.set_parametro(
            'modo_mantenimiento', 
            False, 
            'BOOLEAN', 
            'Activar modo mantenimiento (deshabilita acceso)',
            'SISTEMA'
        )
        
        Parametro.set_parametro(
            'backup_automatico', 
            True, 
            'BOOLEAN', 
            'Realizar backups automáticos de la base de datos',
            'SISTEMA'
        )
        
        # ==================== PARÁMETROS DE REPORTES ====================
        print("📊 6. Creando parámetros de reportes...")
        
        Parametro.set_parametro(
            'incluir_logo_reportes', 
            True, 
            'BOOLEAN', 
            'Incluir logo del edificio en reportes PDF',
            'REPORTES'
        )
        
        Parametro.set_parametro(
            'pie_pagina_reportes', 
            'Edificio Batan 3 - Sistema de Gestión Condominial', 
            'TEXT', 
            'Texto del pie de página en reportes',
            'REPORTES'
        )
        
        # Commit de todos los cambios
        db.session.commit()
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("✅ Seed de parámetros completado exitosamente!")
        print("="*60)
        
        # Contar parámetros por categoría
        categorias = db.session.query(Parametro.categoria, db.func.count(Parametro.id)).group_by(Parametro.categoria).all()
        
        print("\n📊 Resumen de parámetros creados:")
        total = 0
        for categoria, count in categorias:
            print(f"   • {categoria}: {count} parámetros")
            total += count
        print(f"\n   TOTAL: {total} parámetros")
        
        print("\n💡 Puedes consultar los parámetros con:")
        print("   from app.models import Parametro")
        print("   valor = Parametro.get_parametro('clave', 'default')")
        print("\n")

if __name__ == '__main__':
    seed_parametros()
