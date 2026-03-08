"""
MedAssist Export Lambda Function
Generates PDF export of dashboard
Requirements: 13.2-13.5, 20.4
"""
import json
import boto3
import os
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

DOCUMENTS_BUCKET = os.environ.get('DOCUMENTS_BUCKET', 'medassist-documents')
SESSION_TABLE = os.environ.get('SESSION_TABLE', 'MedAssist-Sessions')

DISCLAIMER_TEXT = "This AI system provides informational insights only and does not provide medical diagnosis. Always consult a licensed healthcare professional."

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}

def handler(event, context):
    """
    Generate PDF export of dashboard
    
    Expected input:
    {
        "sessionId": "string",
        "role": "doctor|patient|asha",
        "statCards": [
            {
                "title": "string",
                "value": "string",
                "unit": "string",
                "insight": "string",
                "severity": "normal|warning|critical"
            }
        ]
    }
    """
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('sessionId')
        role = body.get('role', 'patient')
        stat_cards = body.get('statCards', [])
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': {
                        'code': 'MISSING_SESSION_ID',
                        'message': 'Session ID is required',
                        'retryable': False,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            }
        
        # Generate PDF
        pdf_buffer = generate_pdf(session_id, role, stat_cards)
        
        # Upload to S3
        pdf_key = f'sessions/{session_id}/exports/dashboard_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.pdf'
        s3.put_object(
            Bucket=DOCUMENTS_BUCKET,
            Key=pdf_key,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf'
        )
        
        # Generate pre-signed URL (1 hour expiration)
        pdf_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': DOCUMENTS_BUCKET,
                'Key': pdf_key
            },
            ExpiresIn=3600  # 1 hour
        )
        
        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'pdfUrl': pdf_url,
                'expiresAt': expires_at,
                'message': 'PDF generated successfully'
            })
        }
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': {
                    'code': 'PDF_GENERATION_FAILED',
                    'message': 'Unable to generate PDF report. Please try again.',
                    'retryable': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        }

def generate_pdf(session_id, role, stat_cards):
    """Generate PDF document with stat cards"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12
    )
    
    normal_style = styles['Normal']
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # Title
    title = Paragraph("MedAssist AI Health Dashboard", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Metadata
    role_display = role.capitalize() if role != 'asha' else 'ASHA Worker'
    metadata_data = [
        ['Role:', role_display],
        ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')],
        ['Session ID:', session_id[:8] + '...']
    ]
    
    metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(metadata_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Disclaimer
    disclaimer = Paragraph(DISCLAIMER_TEXT, disclaimer_style)
    elements.append(disclaimer)
    elements.append(Spacer(1, 0.3*inch))
    
    # Health Insights Heading
    insights_heading = Paragraph("Health Insights", heading_style)
    elements.append(insights_heading)
    elements.append(Spacer(1, 0.2*inch))
    
    # Stat Cards
    if stat_cards:
        for card in stat_cards:
            elements.append(create_stat_card_element(card))
            elements.append(Spacer(1, 0.2*inch))
    else:
        no_data = Paragraph("No health data available. Please upload medical documents to generate insights.", normal_style)
        elements.append(no_data)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_stat_card_element(card):
    """Create a table element for a stat card"""
    title = card.get('title', 'N/A')
    value = card.get('value', 'N/A')
    unit = card.get('unit', '')
    insight = card.get('insight', '')
    severity = card.get('severity', 'normal')
    
    # Severity color mapping
    severity_colors = {
        'normal': colors.HexColor('#27ae60'),
        'warning': colors.HexColor('#f39c12'),
        'critical': colors.HexColor('#e74c3c')
    }
    severity_color = severity_colors.get(severity, colors.HexColor('#95a5a6'))
    
    # Create card data
    value_text = f"{value} {unit}".strip()
    
    card_data = [
        [Paragraph(f"<b>{title}</b>", getSampleStyleSheet()['Normal'])],
        [Paragraph(f"<font size=18 color='#{severity_color.hexval()[2:]}'><b>{value_text}</b></font>", getSampleStyleSheet()['Normal'])],
        [Paragraph(insight, getSampleStyleSheet()['Normal'])]
    ]
    
    card_table = Table(card_data, colWidths=[6*inch])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    return card_table
