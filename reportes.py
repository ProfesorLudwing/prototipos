"""
reportes.py — Exportación de reportes de 'prototipos'.
Genera CSV, PDF y JPG en memoria (BytesIO), sin tocar el disco.
"""
import csv
import io
from datetime import date
from typing import List

import config
import db
from models import Equipo

# --- reportlab ---
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

# --- Pillow ---
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# Utilidades comunes
# ============================================================
def _encabezados() -> List[str]:
    return [
        "Equipo",
        "Proyecto",
        "Etapa",
        "Integrantes",
        "Área detectada",
        "Entregables entregados",
        "Entregables totales",
    ]


def _fila_de_equipo(eq: Equipo) -> List[str]:
    """Devuelve una fila con los datos clave de un equipo."""
    ents = db.entregables_de_equipo(eq.id)
    entregados = sum(1 for e in ents if e.estado == "entregado")
    return [
        eq.nombre_equipo,
        eq.nombre_proyecto,
        config.ETIQUETA_ETAPA.get(eq.etapa_actual, eq.etapa_actual),
        str(len(eq.integrantes)),
        eq.propuesta.get("dominio_nombre", "—"),
        str(entregados),
        str(len(ents)),
    ]


def _fuente_ttf(tamano: int):
    """
    Intenta cargar una fuente TrueType del sistema.
    Si no encuentra, usa la fuente por defecto de Pillow.
    """
    rutas = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for ruta in rutas:
        try:
            return ImageFont.truetype(ruta, tamano)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ============================================================
# CSV
# ============================================================
def generar_csv_equipos(equipos: List[Equipo]) -> bytes:
    """
    Genera un CSV con una fila por equipo.
    Se devuelve como bytes (con BOM UTF-8 para que Excel lo abra bien).
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_encabezados())
    for eq in equipos:
        writer.writerow(_fila_de_equipo(eq))

    # BOM para que Excel detecte UTF-8 correctamente
    return buffer.getvalue().encode("utf-8-sig")


# ============================================================
# PDF — resumen general
# ============================================================
def generar_pdf_resumen(equipos: List[Equipo]) -> bytes:
    """PDF con la tabla de todos los equipos."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Reporte {config.APP_NOMBRE}",
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Title"],
        fontSize=16,
        spaceAfter=8,
    )
    estilo_sub = ParagraphStyle(
        "Sub",
        parent=estilos["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=14,
    )
    estilo_celda = ParagraphStyle(
        "Celda",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
    )

    elementos = []
    elementos.append(Paragraph(f"Reporte general — {config.APP_NOMBRE}", estilo_titulo))
    elementos.append(Paragraph(
        f"{config.ESCUELA} · Generado el {date.today().isoformat()} · "
        f"Total: {len(equipos)} equipo(s)",
        estilo_sub,
    ))

    # Tabla
    encabezados = _encabezados()
    datos = [[Paragraph(f"<b>{h}</b>", estilo_celda) for h in encabezados]]
    for eq in equipos:
        fila = _fila_de_equipo(eq)
        datos.append([Paragraph(str(c), estilo_celda) for c in fila])

    anchos = [3.0 * cm, 4.5 * cm, 2.5 * cm, 1.8 * cm, 3.2 * cm, 2.2 * cm, 2.0 * cm]
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dee2e6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla)

    # Pie de página
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(
        "Documento de uso interno. Los datos aquí mostrados corresponden "
        "a los equipos registrados en la plataforma.",
        estilo_sub,
    ))

    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ============================================================
# JPG — resumen como imagen
# ============================================================
def generar_jpg_resumen(equipos: List[Equipo]) -> bytes:
    """
    Genera una imagen JPG con la tabla de equipos.
    Se calcula el alto según el número de filas.
    """
    # Configuración de la imagen
    ancho = 1400
    margen = 40
    alto_titulo = 110
    alto_encabezado = 44
    alto_fila = 38
    alto_pie = 50

    filas = [_fila_de_equipo(eq) for eq in equipos]
    alto = alto_titulo + alto_encabezado + alto_fila * max(len(filas), 1) + alto_pie

    img = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(img)

    f_titulo = _fuente_ttf(30)
    f_sub = _fuente_ttf(16)
    f_enc = _fuente_ttf(18)
    f_celda = _fuente_ttf(16)
    f_pie = _fuente_ttf(14)

    # --- Título ---
    draw.text((margen, margen), f"Reporte general — {config.APP_NOMBRE}",
              fill="#0d6efd", font=f_titulo)
    draw.text(
        (margen, margen + 42),
        f"{config.ESCUELA} · {date.today().isoformat()} · {len(equipos)} equipo(s)",
        fill="#6c757d", font=f_sub,
    )

    # --- Tabla ---
    y0 = alto_titulo
    col_x = [margen, 380, 760, 1000, 1100, 1280, 1380]
    # Encabezado
    draw.rectangle([margen, y0, ancho - margen, y0 + alto_encabezado], fill="#0d6efd")
    encabezados = ["Equipo", "Proyecto", "Etapa", "Int.", "Área", "Ent.", "Tot."]
    for i, txt in enumerate(encabezados):
        draw.text((col_x[i] + 8, y0 + 12), txt, fill="white", font=f_enc)

    # Filas
    for idx, fila in enumerate(filas):
        y = y0 + alto_encabezado + idx * alto_fila
        bg = "#f8f9fa" if idx % 2 else "white"
        draw.rectangle([margen, y, ancho - margen, y + alto_fila], fill=bg)
        for i, txt in enumerate(fila):
            # Truncar textos largos
            valor = str(txt)
            limites = [20, 32, 18, 4, 12, 4, 4]
            if len(valor) > limites[i]:
                valor = valor[: limites[i] - 1] + "…"
            draw.text((col_x[i] + 8, y + 10), valor, fill="#212529", font=f_celda)

    # Bordes de la tabla
    y_fin = y0 + alto_encabezado + alto_fila * max(len(filas), 1)
    draw.rectangle([margen, y0, ancho - margen, y_fin], outline="#dee2e6", width=1)
    for i in range(1, len(col_x)):
        draw.line([(col_x[i], y0), (col_x[i], y_fin)], fill="#dee2e6", width=1)

    # --- Pie ---
    draw.text(
        (margen, y_fin + 12),
        "Documento de uso interno · Generado automáticamente por la plataforma.",
        fill="#6c757d", font=f_pie,
    )

    # Guardar como JPG en memoria
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90, optimize=True)
    jpg_bytes = buffer.getvalue()
    buffer.close()
    return jpg_bytes


# ============================================================
# Extra: reporte individual de un equipo (para uso futuro)
# ============================================================
def generar_pdf_equipo(equipo: Equipo) -> bytes:
    """PDF con el detalle completo de un solo equipo."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Reporte {equipo.nombre_equipo}",
    )

    estilos = getSampleStyleSheet()
    estilo_h1 = ParagraphStyle("H1", parent=estilos["Title"], fontSize=18, spaceAfter=6)
    estilo_h2 = ParagraphStyle("H2", parent=estilos["Heading2"], fontSize=12,
                               textColor=colors.HexColor("#0d6efd"), spaceBefore=14,
                               spaceAfter=6)
    estilo_p = ParagraphStyle("P", parent=estilos["Normal"], fontSize=10, leading=14)

    elementos = []
    elementos.append(Paragraph(equipo.nombre_proyecto, estilo_h1))
    elementos.append(Paragraph(
        f"Equipo: <b>{equipo.nombre_equipo}</b> · {config.ESCUELA} · "
        f"Etapa: {config.ETIQUETA_ETAPA.get(equipo.etapa_actual, equipo.etapa_actual)}",
        estilo_p,
    ))

    # Integrantes
    elementos.append(Paragraph("Integrantes", estilo_h2))
    for i in equipo.integrantes:
        elementos.append(Paragraph(f"• {i.nombre} ({i.escuela})", estilo_p))

    # Problemática
    elementos.append(Paragraph("Problemática", estilo_h2))
    elementos.append(Paragraph(equipo.problematica or "(sin definir)", estilo_p))

    # Propuesta
    prop = equipo.propuesta or {}
    if prop:
        elementos.append(Paragraph("Propuesta", estilo_h2))
        elementos.append(Paragraph(
            f"<b>Área:</b> {prop.get('dominio_nombre', '')}", estilo_p,
        ))
        elementos.append(Paragraph(
            f"<b>Objetivo general:</b> {prop.get('objetivo_general', '')}", estilo_p,
        ))
        objetivos = prop.get("objetivos_especificos", [])
        if objetivos:
            elementos.append(Paragraph("<b>Objetivos específicos:</b>", estilo_p))
            for o in objetivos:
                elementos.append(Paragraph(f"• {o}", estilo_p))

    # Entregables
    elementos.append(Paragraph("Entregables", estilo_h2))
    ents = db.entregables_de_equipo(equipo.id)
    if not ents:
        elementos.append(Paragraph("Sin entregables asignados.", estilo_p))
    else:
        for e in ents:
            elementos.append(Paragraph(
                f"• <b>{e.titulo}</b> ({e.etapa}) — límite {e.fecha_limite} "
                f"— <i>{e.estado}</i>",
                estilo_p,
            ))

    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes