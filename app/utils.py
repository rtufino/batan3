from fpdf import FPDF
from io import BytesIO
from flask_mail import Message
from flask import current_app
from app.extensions import mail
from threading import Thread
import locale
import urllib.parse

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
        self.cell(0, 10, 'EDIFICIO BATAN 3', border=0, ln=1, align='C')
        
        self.set_font('Helvetica', '', 10)
        self.cell(0, 5, 'RUC: 1790000000001 | Quito - Ecuador', border=0, ln=1, align='C')
        self.cell(0, 5, 'Comprobante de Transacción', border=0, ln=1, align='C')
        
        # Línea separadora
        self.ln(5)
        self.line(10, 30, 200, 30) # Dibujar línea de margen a margen
        self.ln(10)

    def footer(self):
        # Posición a 1.5 cm del final
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Generado por Sistema Batan3', align='C')

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
    pdf.cell(0, 10, 'EDIFICIO BATAN 3 - AVISO DE COBRO', ln=1, align='C')
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
    # Valor del mes actual
    mes_anio_pdf = movimiento_actual.fecha_emision.strftime('%m / %Y')
    pdf.cell(140, 8, f"Expensa Ordinaria - {mes_anio_pdf}", border=1)
    pdf.cell(50, 8, f"$ {movimiento_actual.monto:.2f}", border=1, ln=1, align='R')

    # Deuda anterior (Saldo pendiente antes de este cargo)
    if deuda_anterior > 0:
        pdf.set_text_color(200, 0, 0) # Rojo para deuda
        pdf.cell(140, 8, "Saldo Pendiente (Meses anteriores)", border=1)
        pdf.cell(50, 8, f"$ {deuda_anterior:.2f}", border=1, ln=1, align='R')
        pdf.set_text_color(0, 0, 0)

    # Total
    pdf.set_font('Helvetica', 'B', 12)
    total = movimiento_actual.monto + deuda_anterior
    pdf.cell(140, 10, "TOTAL A CANCELAR", border=1, fill=True)
    pdf.cell(50, 10, f"$ {total:.2f}", border=1, ln=1, align='R', fill=True)

    # Instrucciones de Pago
    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 5, "INSTRUCCIONES DE PAGO:", ln=1)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, "Favor realizar depósito o transferencia a la Cuenta Corriente del Banco Pichincha Nro. 2100XXXXXX a nombre de EDIFICIO BATAN 3. Enviar el comprobante por los canales oficiales.")

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
    Envía el aviso de cobro mensual al copropietario.
    
    Args:
        departamento: Objeto Departamento
        movimiento: Objeto Movimiento con el cargo generado
        pdf_bytes: Bytes del PDF generado
    """
    # Obtener el propietario o arrendatario responsable
    persona_responsable = None
    
    if departamento.responsable_pago == 'PROPIETARIO':
        persona_responsable = next((p for p in departamento.personas if p.rol == 'PROPIETARIO'), None)
    else:
        persona_responsable = next((p for p in departamento.personas if p.rol == 'ARRENDATARIO'), None)
    
    # Si no hay responsable o no tiene email, no enviar
    if not persona_responsable or not persona_responsable.email or not persona_responsable.recibe_notificaciones:
        return None
    
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
    
    cuerpo_texto = f"""
Estimado/a {persona_responsable.nombre},

Le informamos que se ha generado el aviso de cobro correspondiente al mes de {mes_anio}.

DEPARTAMENTO: {departamento.numero}
MONTO DEL MES: ${movimiento.monto:.2f}
SALDO TOTAL: ${departamento.saldo_pendiente:.2f}

Adjunto encontrará el detalle completo en formato PDF.

Por favor, realice el pago a la brevedad posible según las instrucciones indicadas en el documento.

Atentamente,
Administración Edificio Batan 3
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
        .footer {{ background-color: #95a5a6; color: white; padding: 10px; text-align: center; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EDIFICIO BATAN 3</h1>
        <h2>Aviso de Cobro - {mes_anio}</h2>
    </div>
    
    <div class="content">
        <p>Estimado/a <strong>{persona_responsable.nombre}</strong>,</p>
        
        <p>Le informamos que se ha generado el aviso de cobro correspondiente al mes de <strong>{mes_anio}</strong>.</p>
        
        <div class="info-box">
            <p><strong>DEPARTAMENTO:</strong> {departamento.numero}</p>
            <p><strong>MONTO DEL MES:</strong> <span class="amount">${movimiento.monto:.2f}</span></p>
            <p><strong>SALDO TOTAL:</strong> <span class="amount">${departamento.saldo_pendiente:.2f}</span></p>
        </div>
        
        <p>Adjunto encontrará el detalle completo en formato PDF.</p>
        
        <p>Por favor, realice el pago a la brevedad posible según las instrucciones indicadas en el documento.</p>
        
        <p>Atentamente,<br>
        <strong>Administración Edificio Batan 3</strong></p>
    </div>
    
    <div class="footer">
        <p>Este es un mensaje automático, por favor no responder a este correo.</p>
    </div>
</body>
</html>
"""
    
    # Preparar el adjunto
    mes_anio_file = movimiento.fecha_emision.strftime('%m_%Y')
    nombre_archivo = f"Aviso_Cobro_{departamento.numero}_{mes_anio_file}.pdf"
    adjuntos = [(nombre_archivo, 'application/pdf', pdf_bytes)]
    
    # Enviar el email
    return enviar_email(
        destinatarios=persona_responsable.email,
        asunto=asunto,
        cuerpo_texto=cuerpo_texto,
        cuerpo_html=cuerpo_html,
        adjuntos=adjuntos
    )

def notificar_recibo_pago(departamento, movimiento, pdf_bytes):
    """
    Envía el recibo de pago al copropietario cuando se registra un pago.
    
    Args:
        departamento: Objeto Departamento
        movimiento: Objeto Movimiento con el pago registrado
        pdf_bytes: Bytes del PDF del recibo generado
    """
    # Obtener el propietario o arrendatario responsable
    persona_responsable = None
    
    if departamento.responsable_pago == 'PROPIETARIO':
        persona_responsable = next((p for p in departamento.personas if p.rol == 'PROPIETARIO'), None)
    else:
        persona_responsable = next((p for p in departamento.personas if p.rol == 'ARRENDATARIO'), None)
    
    # Si no hay responsable o no tiene email, no enviar
    if not persona_responsable or not persona_responsable.email or not persona_responsable.recibe_notificaciones:
        return None
    
    # Preparar el contenido del email
    fecha_pago = movimiento.fecha_pago.strftime('%d/%m/%Y')
    
    asunto = f"Recibo de Pago - Departamento {departamento.numero}"
    
    cuerpo_texto = f"""
Estimado/a {persona_responsable.nombre},

Le confirmamos que hemos registrado su pago exitosamente.

DEPARTAMENTO: {departamento.numero}
FECHA DE PAGO: {fecha_pago}
MONTO PAGADO: ${movimiento.monto:.2f}
CONCEPTO: {movimiento.descripcion}

SALDO PENDIENTE ACTUAL: ${departamento.saldo_pendiente:.2f}

Adjunto encontrará el recibo oficial en formato PDF.

Gracias por su puntualidad.

Atentamente,
Administración Edificio Batan 3
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
        <h1>EDIFICIO BATAN 3</h1>
        <h2>Pago Registrado Exitosamente</h2>
    </div>
    
    <div class="content">
        <p>Estimado/a <strong>{persona_responsable.nombre}</strong>,</p>
        
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
        <strong>Administración Edificio Batan 3</strong></p>
    </div>
    
    <div class="footer">
        <p>Este es un mensaje automático, por favor no responder a este correo.</p>
    </div>
</body>
</html>
"""
    
    # Preparar el adjunto
    nombre_archivo = f"Recibo_Pago_{departamento.numero}_{movimiento.id}.pdf"
    adjuntos = [(nombre_archivo, 'application/pdf', pdf_bytes)]
    
    # Enviar el email
    return enviar_email(
        destinatarios=persona_responsable.email,
        asunto=asunto,
        cuerpo_texto=cuerpo_texto,
        cuerpo_html=cuerpo_html,
        adjuntos=adjuntos
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
    print(tel)
    if not tel:
        return None
        
    mensaje = (
        f"Hola {persona.nombre}, le saluda la Administración del Edificio Batan 3. 🏢\n\n"
        f"Le informamos que el estado de cuenta del *Departamento {depto.numero}* presenta un "
        f"valor pendiente de *${monto_total:.2f}*.\n\n"
        f"Agradecemos su gentil pago vía transferencia al Banco Pichincha Cta: 2100XXXXXX.\n"
        f"Por favor, envíenos el comprobante por este medio. ¡Saludos! 👍"
    )
    
    mensaje_codificado = urllib.parse.quote(mensaje)
    return f"https://wa.me/{tel}?text={mensaje_codificado}"