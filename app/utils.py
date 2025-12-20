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
        texto_actor = f"PROPIETARIO DEPARTAMENTO {movimiento.departamento.numero}\n{movimiento.departamento.propietarios[0].nombre}"
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