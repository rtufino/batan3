from fpdf import FPDF
from io import BytesIO

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
    pdf.cell(95, 8, f"FECHA: {movimiento.fecha.strftime('%d/%m/%Y')}", ln=0)
    pdf.cell(95, 8, f"NRO. MOVIMIENTO: #{str(movimiento.id).zfill(6)}", ln=1, align='R')
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
    pdf.cell(0, 5, f"Fecha de Emisión: {movimiento_actual.fecha.strftime('%d/%m/%Y')}", ln=1, align='C')
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
    mes_anio_pdf = movimiento_actual.fecha.strftime('%m / %Y')
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