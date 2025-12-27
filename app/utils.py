from fpdf import FPDF
from io import BytesIO
from flask_mail import Message
from flask import current_app
from app.extensions import mail
from threading import Thread
import locale
import urllib.parse
from app.models import Cuenta, Parametro

# Configurar locale para español (para nombres de meses)
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_EC.UTF-8')
    except:
        pass  # Si no está disponible, usar el locale por defecto

class ReciboPDF(FPDF):
    def header(self):
        # Logo o Título Principal
        self.set_font('Helvetica', 'B', 16)
        # Cell(w, h, txt, border, ln, align)
        self.cell(0, 10, 'EDIFICIO BATAN III', border=0, ln=1, align='C')
        
        self.set_font('Helvetica', '', 10)
        self.cell(0, 5, 'RUC: 1792211255001 | Quito - Ecuador', border=0, ln=1, align='C')
        self.cell(0, 5, 'Comprobante de Transacción', border=0, ln=1, align='C')
        
        # Línea separadora
        self.ln(5)
        self.line(10, 30, 200, 30) # Dibujar línea de margen a margen
        self.ln(10)

    def footer(self):
        # Posición a 1.5 cm del final
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')

def generar_pdf_recibo(movimiento):
    """
    Crea el PDF en memoria y devuelve los bytes.
    """
    pdf = ReciboPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- DATOS DEL ENCABEZADO (Fecha y Numero) ---
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(95, 8, f"FECHA EMISIÓN: {movimiento.fecha_emision.strftime('%d/%m/%Y')}", ln=0)
    pdf.cell(95, 8, f"NRO. MOVIMIENTO: #{str(movimiento.id).zfill(6)}", ln=1, align='R')
    
    # Mostrar fecha de pago si existe
    if movimiento.fecha_pago:
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 6, f"Fecha de Pago: {movimiento.fecha_pago.strftime('%d/%m/%Y')}", ln=1)
    
    pdf.ln(5)

    # --- TIPO Y ESTADO ---
    pdf.set_fill_color(240, 240, 240) # Gris claro
    pdf.set_font('Helvetica', 'B', 11)
    tipo_texto = f"{movimiento.tipo} - {movimiento.estado}"
    pdf.cell(0, 10, tipo_texto, border=1, ln=1, align='C', fill=True)
    pdf.ln(5)

    # --- DATOS DEL ACTOR (Quién paga/recibe) ---
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 8, "RECIBIDO DE / PAGADO A:", ln=1)
    
    pdf.set_font('Helvetica', '', 11)
    if movimiento.departamento:
        texto_actor = f"PROPIETARIO DEPARTAMENTO {movimiento.departamento.numero}\n{movimiento.departamento.personas[0].nombre}"
    elif movimiento.proveedor:
        texto_actor = f"PROVEEDOR: {movimiento.proveedor.nombre}\nDOC: {movimiento.proveedor.ruc_cedula or 'S/N'}"
    else:
        texto_actor = "Administración (Movimiento Interno)"
    
    # Multi_cell para permitir saltos de línea si el nombre es largo
    pdf.multi_cell(0, 8, texto_actor, border='B')
    pdf.ln(5)

    # --- CONCEPTO ---
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 8, "CONCEPTO:", ln=1)
    pdf.set_font('Helvetica', '', 11)
    texto_concepto = f"{movimiento.rubro.nombre}\n{movimiento.descripcion}"
    pdf.multi_cell(0, 8, texto_concepto, border='B')
    pdf.ln(10)

    # --- MONTO TOTAL ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 15, f"VALOR TOTAL: $ {movimiento.monto:.2f} USD", border=1, ln=1, align='C')

    # --- NOTA FINAL ---
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, "Nota: Este documento es un comprobante interno de la administración del edificio. No constituye una factura electrónica autorizada por el SRI salvo que se adjunte el XML correspondiente del proveedor.")

    # Retornar los bytes del PDF
    return BytesIO(pdf.output(dest='S'))

def generar_pdf_aviso(depto, movimiento_actual, deuda_anterior):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'EDIFICIO BATAN III - AVISO DE COBRO', ln=1, align='C')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, f"Fecha de Emisión: {movimiento_actual.fecha_emision.strftime('%d/%m/%Y')}", ln=1, align='C')
    pdf.ln(10)

    # Datos del Departamento y Propietario
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, f" DEPARTAMENTO: {depto.numero}", ln=1, fill=True)
    pdf.set_font('Helvetica', '', 11)
    
    propietario = next((p for p in depto.personas if p.rol == 'PROPIETARIO'), None)
    pdf.cell(0, 8, f"Propietario: {propietario.nombre if propietario else 'S/N'}", ln=1)
    pdf.cell(0, 8, f"Alícuota: {depto.alicuota}%", ln=1)
    pdf.ln(5)

    # Detalle de Valores
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(140, 8, "CONCEPTO", border=1)
    pdf.cell(50, 8, "VALOR", border=1, ln=1, align='C')

    pdf.set_font('Helvetica', '', 11)
    # Valor del mes actual - usar la descripción del movimiento que ya tiene el formato correcto
    pdf.cell(140, 8, movimiento_actual.descripcion, border=1)
    pdf.cell(50, 8, f"$ {movimiento_actual.monto:.2f}", border=1, ln=1, align='R')

    # Deuda anterior (Saldo pendiente antes de este cargo)
    if deuda_anterior > 0:
        pdf.set_text_color(200, 0, 0) # Rojo para deuda
        pdf.cell(140, 8, "Saldo Pendiente (Meses anteriores)", border=1)
        pdf.cell(50, 8, f"$ {deuda_anterior:.2f}", border=1, ln=1, align='R')
        pdf.set_text_color(0, 0, 0)

    # Total
    pdf.set_font('Helvetica', 'B', 12)
    total = float(movimiento_actual.monto) + deuda_anterior
    pdf.cell(140, 10, "TOTAL A CANCELAR", border=1, fill=True)
    pdf.cell(50, 10, f"$ {total:.2f}", border=1, ln=1, align='R', fill=True)

    # Instrucciones de Pago
    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 5, "INSTRUCCIONES DE PAGO:", ln=1)
    pdf.set_font('Helvetica', '', 9)
    
    # Buscar la cuenta del Banco Pichincha
    cuenta_pichincha = Cuenta.query.filter(Cuenta.nombre.ilike('%pichincha%')).first()
    
    if cuenta_pichincha and cuenta_pichincha.numero:
        instrucciones = f"Favor realizar deposito o transferencia a la Cuenta Corriente del {cuenta_pichincha.nombre} Nro. {cuenta_pichincha.numero} a nombre de Mayra Araujo.\n\nEnviar el comprobante de pago al WhatsApp: 0992923858 o al correo: edificio.batan3@gmail.com"
    else:
        instrucciones = "Favor realizar deposito o transferencia a la Cuenta Corriente del Banco Pichincha a nombre de Mayra Araujo.\n\nEnviar el comprobante de pago al WhatsApp: 0992923858 o al correo: edificio.batan3@gmail.com"
    
    pdf.multi_cell(0, 5, instrucciones)
    
    # Recordatorio en rojo
    pdf.ln(10)
    pdf.set_text_color(200, 0, 0)  # Rojo
    pdf.set_font('Helvetica', 'B', 10)
    pdf.multi_cell(0, 6, "RECUERDE: Realizar el pago de su expensa dentro de los primeros 15 días del mes.", border=1, align='C', fill=False)
    pdf.set_text_color(0, 0, 0)  # Volver a negro

    return pdf.output(dest='S') # Retornamos los bytes

# --- FUNCIONES DE NOTIFICACIÓN POR EMAIL ---

def enviar_email_async(app, msg):
    """
    Envía el email en un hilo separado para no bloquear la aplicación.
    """
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            # Log del error (en producción deberías usar logging)
            print(f"Error al enviar email: {str(e)}")

def enviar_email(destinatarios, asunto, cuerpo_texto, cuerpo_html=None, adjuntos=None):
    """
    Función genérica para enviar emails.
    
    Args:
        destinatarios: Lista de emails o un solo email (string)
        asunto: Asunto del email
        cuerpo_texto: Versión en texto plano del mensaje
        cuerpo_html: Versión HTML del mensaje (opcional)
        adjuntos: Lista de tuplas (nombre_archivo, tipo_mime, datos_bytes)
    """
    app = current_app._get_current_object()
    
    # Asegurar que destinatarios sea una lista
    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]
    
    # Crear el mensaje
    msg = Message(
        subject=app.config['MAIL_SUBJECT_PREFIX'] + asunto,
        recipients=destinatarios,
        body=cuerpo_texto,
        html=cuerpo_html,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    
    # Adjuntar archivos si existen
    if adjuntos:
        for nombre, tipo_mime, datos in adjuntos:
            msg.attach(nombre, tipo_mime, datos)
    
    # Enviar en un hilo separado
    thread = Thread(target=enviar_email_async, args=(app, msg))
    thread.start()
    
    return thread

def notificar_aviso_cobro(departamento, movimiento, pdf_bytes):
    """
    Envía el aviso de cobro mensual a todas las personas relacionadas con el departamento.
    
    Args:
        departamento: Objeto Departamento
        movimiento: Objeto Movimiento con el cargo generado
        pdf_bytes: Bytes del PDF generado
    """
    # Obtener todas las personas que reciben notificaciones
    personas_notificar = [p for p in departamento.personas if p.recibe_notificaciones and p.email]
    
    # Si no hay nadie para notificar, retornar
    if not personas_notificar:
        return None
    
    # Obtener emails de todas las personas
    destinatarios = [p.email for p in personas_notificar]
    
    # Usar el nombre del primer contacto para el saludo
    nombre_saludo = personas_notificar[0].nombre
    
    # Preparar el contenido del email
    # Obtener mes y año en español
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    mes_nombre = meses_es[movimiento.fecha_emision.month]
    mes_anio = f"{mes_nombre} {movimiento.fecha_emision.year}"
    
    asunto = f"Aviso de Cobro - {mes_anio}"
    
    # Buscar la cuenta del Banco Pichincha
    cuenta_pichincha = Cuenta.query.filter(Cuenta.nombre.ilike('%pichincha%')).first()

    # Parametros
    whatsapp = Parametro.get_parametro('whatsapp_administracion', '0992923858')
    email = Parametro.get_parametro('email_administracion', 'edificio.batan3@gmail.com')
    
    cuerpo_texto = f"""
Estimado/a {nombre_saludo},

Le informamos que se ha generado el aviso de cobro correspondiente al mes de {mes_anio}.

DEPARTAMENTO: {departamento.numero}
MONTO DEL MES: ${movimiento.monto:.2f}
SALDO TOTAL: ${departamento.saldo_pendiente:.2f}

RECUERDE: Realizar el pago de su expensa dentro de los primeros 15 días del mes.

Favor realizar deposito o transferencia a la Cuenta Corriente del {cuenta_pichincha.nombre} Nro. {cuenta_pichincha.numero} a nombre de Mayra Araujo.

Enviar el comprobante de pago al WhatsApp: {whatsapp} o al correo: {email}"

Atentamente,
Administración Edificio Batan III
"""
    
    cuerpo_html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .info-box {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .amount {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
        .reminder {{ background-color: #ffebee; color: #c62828; padding: 15px; border-left: 5px solid #c62828; margin: 20px 0; font-weight: bold; text-align: center; }}
        .footer {{ background-color: #95a5a6; color: white; padding: 10px; text-align: center; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EDIFICIO BATAN III</h1>
        <h2>Aviso de Cobro - {mes_anio}</h2>
    </div>
    
    <div class="content">
        <p>Estimado/a <strong>{nombre_saludo}</strong>,</p>
        
        <p>Le informamos que se ha generado el aviso de cobro correspondiente al mes de <strong>{mes_anio}</strong>.</p>
        
        <div class="info-box">
            <p><strong>DEPARTAMENTO:</strong> {departamento.numero}</p>
            <p><strong>MONTO DEL MES:</strong> <span class="amount">${movimiento.monto:.2f}</span></p>
            <p><strong>SALDO TOTAL:</strong> <span class="amount">${departamento.saldo_pendiente:.2f}</span></p>
        </div>
        
        <div class="reminder">
            ⚠️ RECUERDE: Realizar el pago de su expensa dentro de los primeros 15 días del mes.
        </div>
        
        <p>Adjunto encontrará el detalle completo en formato PDF.</p>
         
        <p>Atentamente,<br>
        <strong>Administración Edificio Batan III</strong></p>
    </div>
    
    <div class="footer">
        <p>Este es un mensaje automático generado por el Sistema de Administración.</p>
    </div>
</body>
</html>
"""
    
    # Preparar el adjunto
    mes_anio_file = movimiento.fecha_emision.strftime('%m_%Y')
    nombre_archivo = f"Aviso_Cobro_{departamento.numero}_{mes_anio_file}.pdf"
    adjuntos = [(nombre_archivo, 'application/pdf', pdf_bytes)]
    
    # 1. Obtención de parámetros de configuración
    enviar_adjunto = Parametro.get_parametro('enviar_adjunto', False)
    enviar_html = Parametro.get_parametro('enviar_html', False)

    # 2. Lógica de filtrado eficiente
    # Si enviar_html es False, forzamos cuerpo_html a None
    html_final = cuerpo_html if enviar_html else None

    # Si enviar_adjunto es False, enviamos una lista vacía o None
    adjuntos_final = adjuntos if enviar_adjunto else None

    # 3. Retorno de la función con los datos filtrados
    return enviar_email(
        destinatarios=destinatarios,
        asunto=asunto,
        cuerpo_texto=cuerpo_texto,
        cuerpo_html=html_final,
        adjuntos=adjuntos_final
    )

def notificar_recibo_pago(departamento, movimiento, pdf_bytes):
    """
    Envía el recibo de pago a todas las personas relacionadas con el departamento.
    
    Args:
        departamento: Objeto Departamento
        movimiento: Objeto Movimiento con el pago registrado
        pdf_bytes: Bytes del PDF del recibo generado
    """
    # Obtener todas las personas que reciben notificaciones
    personas_notificar = [p for p in departamento.personas if p.recibe_notificaciones and p.email]
    
    # Si no hay nadie para notificar, retornar
    if not personas_notificar:
        return None
    
    # Obtener emails de todas las personas
    destinatarios = [p.email for p in personas_notificar]
    
    # Usar el nombre del primer contacto para el saludo
    nombre_saludo = personas_notificar[0].nombre
    
    # Preparar el contenido del email
    fecha_pago = movimiento.fecha_pago.strftime('%d/%m/%Y')
    
    asunto = f"Recibo de Pago - Departamento {departamento.numero}"
    
    cuerpo_texto = f"""
Estimado/a {nombre_saludo},

Le confirmamos que hemos registrado su pago exitosamente.

DEPARTAMENTO: {departamento.numero}
FECHA DE PAGO: {fecha_pago}
MONTO PAGADO: ${movimiento.monto:.2f}
CONCEPTO: {movimiento.descripcion}

SALDO PENDIENTE ACTUAL: ${departamento.saldo_pendiente:.2f}

Gracias por su puntualidad.

Atentamente,
Administración Edificio Batan III
"""
    
    cuerpo_html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .info-box {{ background-color: #d5f4e6; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #27ae60; }}
        .amount {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
        .footer {{ background-color: #95a5a6; color: white; padding: 10px; text-align: center; font-size: 12px; }}
        .checkmark {{ font-size: 48px; color: #27ae60; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="checkmark">✓</div>
        <h1>EDIFICIO BATAN III</h1>
        <h2>Pago Registrado Exitosamente</h2>
    </div>
    
    <div class="content">
        <p>Estimado/a <strong>{nombre_saludo}</strong>,</p>
        
        <p>Le confirmamos que hemos registrado su pago exitosamente.</p>
        
        <div class="info-box">
            <p><strong>DEPARTAMENTO:</strong> {departamento.numero}</p>
            <p><strong>FECHA DE PAGO:</strong> {fecha_pago}</p>
            <p><strong>MONTO PAGADO:</strong> <span class="amount">${movimiento.monto:.2f}</span></p>
            <p><strong>CONCEPTO:</strong> {movimiento.descripcion}</p>
            <hr>
            <p><strong>SALDO PENDIENTE ACTUAL:</strong> ${departamento.saldo_pendiente:.2f}</p>
        </div>
        
        <p>Adjunto encontrará el recibo oficial en formato PDF.</p>
        
        <p><strong>Gracias por su puntualidad.</strong></p>
        
        <p>Atentamente,<br>
        <strong>Administración Edificio Batan III</strong></p>
    </div>
    
    <div class="footer">
        <p>Este es un mensaje automático generado por el Sistema de Administración.</p>
    </div>
</body>
</html>
"""
    
    # Preparar el adjunto
    nombre_archivo = f"Recibo_Pago_{departamento.numero}_{movimiento.id}.pdf"
    adjuntos = [(nombre_archivo, 'application/pdf', pdf_bytes)]
    
    # 1. Obtención de parámetros de configuración
    enviar_adjunto = Parametro.get_parametro('enviar_adjunto', False)
    enviar_html = Parametro.get_parametro('enviar_html', False)

    # 2. Lógica de filtrado eficiente
    # Si enviar_html es False, forzamos cuerpo_html a None
    html_final = cuerpo_html if enviar_html else None

    # Si enviar_adjunto es False, enviamos una lista vacía o None
    adjuntos_final = adjuntos if enviar_adjunto else None

    # 3. Retorno de la función con los datos filtrados
    return enviar_email(
        destinatarios=destinatarios,
        asunto=asunto,
        cuerpo_texto=cuerpo_texto,
        cuerpo_html=html_final,
        adjuntos=adjuntos_final
    )

def formatear_telefono_whatsapp(telefono):
    """
    Limpia y formatea el número para WhatsApp.
    Si empieza con '0', asume que es local (Ecuador) y pone +593.
    """
    if not telefono:
        return ""
    
    # Quitamos espacios y guiones para estandarizar
    tel_limpio = telefono.replace(" ", "").replace("-", "")
    
    # Si el número empieza con '0' y tiene 10 dígitos (formato estándar Ecuador)
    if tel_limpio.startswith("0"):
        # Reemplazamos solo el primer '0' por '+593'
        tel_limpio = "+593" + tel_limpio[1:]
    
    return tel_limpio

def generar_link_whatsapp(persona, depto, monto_total):
    tel = formatear_telefono_whatsapp(persona.telefono)
    if not tel:
        return None
    
    cuenta_pichincha = Cuenta.query.filter(Cuenta.nombre.ilike('%pichincha%')).first()
        
    mensaje = (
        f"Hola {persona.nombre}, le saluda la Administración del Edificio Batan III. \n\n"
        f"Le informamos que el estado de cuenta del *Departamento {depto.numero}* presenta un "
        f"valor pendiente de *${monto_total:.2f}*.\n\n"
        f"Favor realizar deposito o transferencia a la Cuenta Corriente del {cuenta_pichincha.nombre} Nro. {cuenta_pichincha.numero} a nombre de Mayra Araujo.\n"
        f"Por favor, envíenos el comprobante por este medio. ¡Saludos!"
    )
    
    mensaje_codificado = urllib.parse.quote(mensaje)
    return f"https://wa.me/{tel}?text={mensaje_codificado}"

def generar_pdf_estado_cuenta(depto, movimientos):
    """
    Genera un PDF con el estado de cuenta del departamento y los últimos movimientos.
    Todo en una sola página A4 vertical.
    
    Args:
        depto: Objeto Departamento
        movimientos: Lista de movimientos (máximo 12)
    
    Returns:
        bytes del PDF generado
    """
    from datetime import datetime
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)  # Desactivar salto automático para controlar el espacio
    
    # --- ENCABEZADO ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 8, 'EDIFICIO BATAN III', ln=1, align='C')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 5, 'RUC: 1792211255001 | Quito - Ecuador', ln=1, align='C')
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 6, 'ESTADO DE CUENTA', ln=1, align='C')
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(0, 4, f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
    pdf.ln(3)
    
    # --- INFORMACIÓN DEL DEPARTAMENTO ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, f"DEPARTAMENTO: {depto.numero}", ln=1, fill=True)
    
    pdf.set_font('Helvetica', '', 9)
    propietario = next((p for p in depto.personas if p.rol == 'PROPIETARIO'), None)
    if propietario:
        pdf.cell(0, 5, f"Propietario: {propietario.nombre}", ln=1)
    
    pdf.cell(95, 5, f"Piso: {depto.piso if depto.piso > 0 else 'Planta Baja'}", ln=0)
    pdf.cell(95, 5, f"Alícuota: {depto.alicuota}%", ln=1)
    
    # Saldo pendiente destacado
    pdf.ln(2)
    if depto.saldo_pendiente > 0:
        pdf.set_fill_color(255, 235, 238)  # Rojo claro
        pdf.set_text_color(200, 0, 0)  # Rojo
    else:
        pdf.set_fill_color(212, 237, 218)  # Verde claro
        pdf.set_text_color(0, 128, 0)  # Verde
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, f"SALDO PENDIENTE: $ {depto.saldo_pendiente:.2f}", ln=1, align='C', fill=True, border=1)
    pdf.set_text_color(0, 0, 0)  # Volver a negro
    pdf.ln(3)
    
    # --- HISTORIAL DE MOVIMIENTOS ---
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, "ÚLTIMOS MOVIMIENTOS (Máximo 12)", ln=1)
    pdf.ln(1)
    
    # Encabezados de tabla
    pdf.set_fill_color(52, 73, 94)  # Azul oscuro
    pdf.set_text_color(255, 255, 255)  # Blanco
    pdf.set_font('Helvetica', 'B', 8)
    
    pdf.cell(22, 6, "F. Emisión", border=1, align='C', fill=True)
    pdf.cell(22, 6, "F. Pago", border=1, align='C', fill=True)
    pdf.cell(70, 6, "Descripción", border=1, align='C', fill=True)
    pdf.cell(20, 6, "Estado", border=1, align='C', fill=True)
    pdf.cell(25, 6, "Monto", border=1, align='C', fill=True)
    pdf.cell(31, 6, "Rubro", border=1, align='C', fill=True, ln=1)
    
    # Resetear colores para el contenido
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 7)
    
    # Limitar a 12 movimientos para que quepa en una página
    movimientos_mostrar = movimientos[:12] if len(movimientos) > 12 else movimientos
    
    for mov in movimientos_mostrar:
        # Alternar color de fondo
        if movimientos_mostrar.index(mov) % 2 == 0:
            pdf.set_fill_color(255, 255, 255)  # Blanco
        else:
            pdf.set_fill_color(245, 245, 245)  # Gris muy claro
        
        # Fecha emisión
        pdf.cell(22, 5, mov.fecha_emision.strftime('%d/%m/%Y'), border=1, align='C', fill=True)
        
        # Fecha pago
        fecha_pago_str = mov.fecha_pago.strftime('%d/%m/%Y') if mov.fecha_pago else '-'
        pdf.cell(22, 5, fecha_pago_str, border=1, align='C', fill=True)
        
        # Descripción (truncar si es muy larga)
        descripcion = mov.descripcion[:35] + '...' if len(mov.descripcion) > 35 else mov.descripcion
        pdf.cell(70, 5, descripcion, border=1, fill=True)
        
        # Estado
        estado_texto = 'PAGADO' if mov.estado == 'PAGADO' else 'PENDIENTE'
        pdf.cell(20, 5, estado_texto, border=1, align='C', fill=True)
        
        # Monto (con color según estado)
        if mov.estado == 'PENDIENTE':
            pdf.set_text_color(200, 0, 0)  # Rojo para pendiente
            monto_texto = f"+ ${mov.monto:.2f}"
        else:
            pdf.set_text_color(0, 128, 0)  # Verde para pagado
            monto_texto = f"- ${mov.monto:.2f}"
        
        pdf.cell(25, 5, monto_texto, border=1, align='R', fill=True)
        pdf.set_text_color(0, 0, 0)  # Volver a negro
        
        # Rubro (truncar si es muy largo)
        rubro_nombre = mov.rubro.nombre[:15] + '...' if len(mov.rubro.nombre) > 15 else mov.rubro.nombre
        pdf.cell(31, 5, rubro_nombre, border=1, align='C', fill=True, ln=1)
    
    # Si no hay movimientos
    if not movimientos_mostrar:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 8, "No hay movimientos registrados", border=1, align='C', ln=1)
    
    # --- PIE DE PÁGINA ---
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(128, 128, 128)  # Gris
    pdf.multi_cell(0, 3, "Nota: Este documento es un estado de cuenta informativo generado por el sistema de administración del Edificio Batan III. Para consultas o aclaraciones, contactar a edificio.batan3@gmail.com o WhatsApp: 0992923858")
    
    # Línea de generación
    pdf.ln(2)
    pdf.cell(0, 3, f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}", align='C')
    
    return pdf.output(dest='S')