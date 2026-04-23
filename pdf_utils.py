from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import base64

def gerar_pdf_tabela(dados, titulo, modo_paisagem=False):
    buffer = BytesIO()
    tamanho_pagina = landscape(letter) if modo_paisagem else letter
    doc = SimpleDocTemplate(buffer, pagesize=tamanho_pagina)
    styles = getSampleStyleSheet()
    elements = [Paragraph(titulo, styles['Title']), Spacer(1, 12)]
    
    t = Table(dados)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8) 
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def gerar_pdf_simples(titulo, linhas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph(titulo, styles['Title']), Spacer(1, 20)]
    for linha in linhas:
        elements.append(Paragraph(linha, styles['Normal']))
        elements.append(Spacer(1, 10))
    doc.build(elements)
    buffer.seek(0)
    return buffer

def gerar_pdf_os_modelo(dados_os, itens):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>{dados_os['tipo'].upper()}</b> - Nº {dados_os['id']}", styles['Title']))
    elements.append(Paragraph(f"Data: {dados_os['data']}", styles['Normal']))
    elements.append(Spacer(1, 10))

    setor = dados_os.get('endereco', '') 
    
    dados_cliente = [
        [f"Solicitante: {dados_os['nome']}", f"Fone: {dados_os['fone']}"],
        [f"Setor: {setor}", f"Celular: {dados_os['celular']}"],
        [f"CNPJ/Matrícula: {dados_os['cnpj']}", f"Equip./Modelo: {dados_os['modelo']}"]
    ]
    t_cliente = Table(dados_cliente, colWidths=[300, 200])
    t_cliente.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black), 
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6)
    ]))
    elements.append(t_cliente)
    elements.append(Spacer(1, 15))

    dados_itens = [["Quant.", "Discriminação"]]
    for item in itens:
        dados_itens.append([str(item.get('Quant.', '')), item.get('Discriminação', '')])
    
    t_itens = Table(dados_itens, colWidths=[60, 440])
    t_itens.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ]))
    elements.append(t_itens)
    elements.append(Spacer(1, 20))

    # --- NOVO: IMPRIME O PARECER TÉCNICO SE EXISTIR ---
    parecer = dados_os.get('parecer_tecnico')
    if parecer and str(parecer).strip() and str(parecer) != 'None':
        elements.append(Paragraph("<b>Parecer Técnico / Resolução:</b>", styles['Normal']))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(str(parecer), styles['Normal']))
        elements.append(Spacer(1, 20))

    # Renderiza a imagem se existir
    imagem_b64 = dados_os.get('imagem_base64')
    if imagem_b64:
        try:
            img_data = base64.b64decode(imagem_b64)
            img_buffer = BytesIO(img_data)
            img = Image(img_buffer, width=250, height=200) 
            elements.append(Paragraph("<b>Registro Fotográfico:</b>", styles['Normal']))
            elements.append(Spacer(1, 5))
            elements.append(img)
            elements.append(Spacer(1, 20))
        except Exception as e:
            elements.append(Paragraph("(Erro ao carregar a foto anexada)", styles['Normal']))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("____________________________________________________", styles['Normal']))
    elements.append(Paragraph("Assinatura do Responsável", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer