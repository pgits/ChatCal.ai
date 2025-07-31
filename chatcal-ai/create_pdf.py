#!/usr/bin/env python3
"""Generate PDF version of ChatCal LinkedIn diagram."""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors

def create_pdf():
    """Create PDF version of ChatCal LinkedIn diagram."""
    # Create PDF document
    doc = SimpleDocTemplate(
        "CHATCAL_LINKEDIN_DIAGRAM.pdf",
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#2c3e50')
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=15,
        spaceBefore=20,
        textColor=HexColor('#3498db'),
        alignment=TA_CENTER
    )
    
    feature_title_style = ParagraphStyle(
        'FeatureTitle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=10,
        textColor=HexColor('#2c3e50')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=15
    )
    
    # Story elements
    story = []
    
    # Title
    story.append(Paragraph("🤖 ChatCal.ai", title_style))
    story.append(Paragraph("AI-Powered Scheduling Assistant for Peter Michael Gits", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Core Features Section
    story.append(Paragraph("🎯 CORE FEATURES", header_style))
    
    # Create features table
    features_data = [
        ["Natural Language Processing", "Smart Contact Collection"],
        ["• \"Book 15 mins with Peter\"", "• Name + Email OR Phone required"],
        ["• \"Tomorrow at 2pm works\"", "• Flexible requirements"],
        ["", "• Peter's contact always available"],
        ["", ""],
        ["Intelligent Time Management", "Multi-Format Meeting Support"],
        ["• Real-time availability", "• Business consultations (60 min)"],
        ["• Conflict detection", "• Quick discussions (30 min)"],
        ["• Auto-scheduling", "• Project meetings (60 min)"],
        ["", "• Advisory sessions (90 min)"]
    ]
    
    features_table = Table(features_data, colWidths=[3*inch, 3*inch])
    features_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8f5e9')),
        ('BACKGROUND', (0, 5), (-1, 5), HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#ddd'))
    ]))
    
    story.append(features_table)
    story.append(Spacer(1, 20))
    
    # Google Meet Integration
    story.append(Paragraph("🎥 GOOGLE MEET INTEGRATION", header_style))
    story.append(Paragraph("• Automatic Video Conference Creation", normal_style))
    story.append(Paragraph("• Detects: \"Google Meet\", \"video call\", \"online meeting\"", normal_style))
    story.append(Paragraph("• Real Google Meet links generated automatically", normal_style))
    story.append(Paragraph("• Works with all meeting types", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>Example Request:</b>", feature_title_style))
    story.append(Paragraph("\"Hi, I need a Google Meet call with Peter tomorrow at 3pm\"", normal_style))
    story.append(Paragraph("<b>Result:</b> ✅ Meeting scheduled ✅ Google Meet link: meet.google.com/abc-def-ghi", normal_style))
    story.append(Spacer(1, 20))
    
    # Email System
    story.append(Paragraph("📧 EMAIL SYSTEM", header_style))
    email_data = [
        ["Dual Email Invitations", "Rich Calendar Attachments"],
        ["• Sent to both Peter & user", "• .ics calendar files"],
        ["• Professional HTML templates", "• Google Meet links included"],
        ["• Automatic after booking", "• Complete meeting details"],
        ["", ""],
        ["Smart Email Collection", "Branded Communication"],
        ["• \"Want email invitation?\"", "• ChatCal.ai branding"],
        ["• Optional but encouraged", "• Professional formatting"]
    ]
    
    email_table = Table(email_data, colWidths=[3*inch, 3*inch])
    email_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#fff3cd')),
        ('BACKGROUND', (0, 5), (-1, 5), HexColor('#fff3cd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#ddd'))
    ]))
    
    story.append(email_table)
    story.append(Spacer(1, 20))
    
    # AI Capabilities
    story.append(Paragraph("🧠 AI CAPABILITIES", header_style))
    ai_data = [
        ["Claude Sonnet 4 Integration", "Context-Aware Conversations"],
        ["• Latest Anthropic AI model", "• Remembers user details"],
        ["• Advanced reasoning", "• Maintains conversation flow"],
        ["• Professional responses", "• Handles complex requests"],
        ["", ""],
        ["Information Extraction", "Intelligent Error Handling"],
        ["• Names from \"This is Betty\"", "• Graceful conflict resolution"],
        ["• Phone: \"call me at 555...\"", "• Alternative time suggestions"],
        ["• Complex multi-part requests", "• User-friendly error messages"]
    ]
    
    ai_table = Table(ai_data, colWidths=[3*inch, 3*inch])
    ai_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e3f2fd')),
        ('BACKGROUND', (0, 5), (-1, 5), HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#ddd'))
    ]))
    
    story.append(ai_table)
    story.append(Spacer(1, 20))
    
    # Setup Guide
    story.append(Paragraph("📋 SETUP GUIDE", header_style))
    story.append(Paragraph("<b>1️⃣ Prerequisites</b>", feature_title_style))
    story.append(Paragraph("• Python 3.9+", normal_style))
    story.append(Paragraph("• Google Cloud Project", normal_style))
    story.append(Paragraph("• Anthropic API key", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>2️⃣ Google Calendar Setup</b>", feature_title_style))
    story.append(Paragraph("• Enable Google Calendar API", normal_style))
    story.append(Paragraph("• Create OAuth2 credentials", normal_style))
    story.append(Paragraph("• Run: python3 complete_oauth.py", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>3️⃣ Environment Configuration</b>", feature_title_style))
    story.append(Paragraph("• Copy .env.example to .env", normal_style))
    story.append(Paragraph("• Add ANTHROPIC_API_KEY=your_key_here", normal_style))
    story.append(Paragraph("• Add GOOGLE_CALENDAR_ID=your_email@gmail.com", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>4️⃣ Dependencies & Launch</b>", feature_title_style))
    story.append(Paragraph("• pip install -r requirements.txt", normal_style))
    story.append(Paragraph("• python3 -m uvicorn app.api.main:app --reload", normal_style))
    story.append(Paragraph("• Visit: http://localhost:8000/simple-chat", normal_style))
    story.append(Spacer(1, 20))
    
    # Usage Examples
    story.append(Paragraph("💡 USAGE EXAMPLES", header_style))
    story.append(Paragraph("<b>User:</b> \"Book 15 minutes with Peter, this is Betty, have him call me at 630 880 5488 Friday, please show me available morning times\"", normal_style))
    story.append(Paragraph("<b>ChatCal:</b> ✅ Name: Betty ✅ Phone: 630-880-5488<br/>\"Here are Friday morning slots: 9:00 AM, 10:30 AM, 11:00 AM\"", normal_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>User:</b> \"I need a Google Meet with Peter Wednesday at 2pm for an hour\"", normal_style))
    story.append(Paragraph("<b>ChatCal:</b> ✅ Meeting booked ✅ Google Meet: meet.google.com/xyz-abc-123<br/>📧 Email invitations sent to both parties", normal_style))
    story.append(Spacer(1, 20))
    
    # Technical Architecture
    story.append(Paragraph("🔧 TECHNICAL ARCHITECTURE", header_style))
    tech_data = [
        ["Backend", "Frontend"],
        ["• FastAPI REST API", "• Simple HTML/JS chat interface"],
        ["• Redis session management", "• Real-time messaging"],
        ["• Google Calendar API", "• Mobile-responsive design"],
        ["• SMTP email service", "• Clean, professional UI"],
        ["", ""],
        ["AI & Integration", "Deployment"],
        ["• LlamaIndex ReActAgent", "• Docker containerization"],
        ["• Anthropic Claude Sonnet 4", "• Environment-based config"],
        ["• Google OAuth2 authentication", "• Production-ready setup"]
    ]
    
    tech_table = Table(tech_data, colWidths=[3*inch, 3*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f1f8ff')),
        ('BACKGROUND', (0, 6), (-1, 6), HexColor('#f1f8ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#ddd'))
    ]))
    
    story.append(tech_table)
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph("Built with ❤️ using Claude Sonnet 4, Google Calendar API, and modern Python", 
                          ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, 
                                       fontSize=12, textColor=HexColor('#666'))))
    
    # Build PDF
    doc.build(story)
    print("✅ PDF created successfully: CHATCAL_LINKEDIN_DIAGRAM.pdf")

if __name__ == "__main__":
    create_pdf()