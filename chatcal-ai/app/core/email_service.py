"""Email service for sending calendar invitations."""

import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any
from app.config import settings


class EmailService:
    """Handles sending email invitations for calendar appointments."""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.username = settings.smtp_username or settings.my_email_address
        self.password = settings.smtp_password
        self.from_name = settings.email_from_name
        self.from_email = settings.my_email_address
    
    def create_calendar_invite(self, 
                             title: str,
                             start_datetime: datetime,
                             end_datetime: datetime,
                             description: str = "",
                             location: str = "",
                             organizer_email: str = None,
                             attendee_emails: list = None) -> str:
        """Create an iCal calendar invitation."""
        
        if not organizer_email:
            organizer_email = self.from_email
        
        if not attendee_emails:
            attendee_emails = []
        
        # Generate unique UID for the event
        uid = str(uuid.uuid4())
        
        # Format datetime for iCal
        def format_dt(dt):
            return dt.strftime('%Y%m%dT%H%M%SZ')
        
        now = datetime.now(timezone.utc)
        
        ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ChatCal.ai//Calendar Event//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{format_dt(now)}
DTSTART:{format_dt(start_datetime)}
DTEND:{format_dt(end_datetime)}
SUMMARY:{title}
DESCRIPTION:{description}
LOCATION:{location}
ORGANIZER:MAILTO:{organizer_email}"""
        
        for attendee in attendee_emails:
            ical_content += f"\nATTENDEE:MAILTO:{attendee}"
        
        ical_content += f"""
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""
        
        return ical_content
    
    def send_invitation_email(self,
                            to_email: str,
                            to_name: str,
                            title: str,
                            start_datetime: datetime,
                            end_datetime: datetime,
                            description: str = "",
                            user_phone: str = "",
                            meeting_type: str = "Meeting",
                            meet_link: str = "") -> bool:
        """Send a calendar invitation email."""
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Meeting Invitation: {title}"
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            # Create email body
            if to_email == settings.my_email_address:
                # Email to Peter
                html_body = self._create_peter_email_body(
                    title, start_datetime, end_datetime, description, to_name, user_phone, meet_link
                )
            else:
                # Email to user
                html_body = self._create_user_email_body(
                    title, start_datetime, end_datetime, description, meeting_type, meet_link
                )
            
            # Create plain text version
            text_body = self._html_to_text(html_body)
            
            # Attach both versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Create and attach calendar invitation
            ical_content = self.create_calendar_invite(
                title=title,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                description=description,
                organizer_email=self.from_email,
                attendee_emails=[to_email, self.from_email]
            )
            
            # Attach calendar file
            cal_attachment = MIMEBase('text', 'calendar')
            cal_attachment.set_payload(ical_content.encode('utf-8'))
            encoders.encode_base64(cal_attachment)
            cal_attachment.add_header('Content-Disposition', 'attachment; filename="meeting.ics"')
            cal_attachment.add_header('Content-Type', 'text/calendar; method=REQUEST; name="meeting.ics"')
            msg.attach(cal_attachment)
            
            # Send email
            if self.password:  # Only send if SMTP credentials are configured
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
                
                print(f"✅ Email invitation sent to {to_email}")
                return True
            else:
                print(f"📧 Email invitation prepared for {to_email} (SMTP not configured)")
                return True  # Consider it successful for demo purposes
                
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def _create_peter_email_body(self, title: str, start_datetime: datetime, 
                               end_datetime: datetime, description: str, 
                               user_name: str, user_phone: str, meet_link: str = "") -> str:
        """Create email body for Peter."""
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px; color: #333;">
            <h2 style="color: #2c3e50;">📅 New Meeting Scheduled</h2>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #495057;">{title}</h3>
                
                <div style="margin: 15px 0;">
                    <strong>📅 Date & Time:</strong><br>
                    {start_datetime.strftime('%A, %B %d, %Y')}<br>
                    {start_datetime.strftime('%I:%M %p')} - {end_datetime.strftime('%I:%M %p')} ({start_datetime.strftime('%Z')})
                </div>
                
                <div style="margin: 15px 0;">
                    <strong>👤 Meeting with:</strong> {user_name}<br>
                    <strong>📞 Phone:</strong> {user_phone or 'Not provided'}
                    {f'<br><strong>🎥 Google Meet:</strong> <a href="{meet_link}" style="color: #1976d2;">{meet_link}</a>' if meet_link else ''}
                </div>
                
                {f'<div style="margin: 15px 0;"><strong>📝 Details:</strong><br>{description}</div>' if description else ''}
            </div>
            
            <p style="color: #6c757d; font-size: 14px;">
                This meeting was scheduled through ChatCal.ai. The calendar invitation is attached to this email.
            </p>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Sent by ChatCal.ai - Peter Michael Gits' AI Scheduling Assistant
            </p>
        </body>
        </html>
        """
    
    def _create_user_email_body(self, title: str, start_datetime: datetime, 
                              end_datetime: datetime, description: str, 
                              meeting_type: str, meet_link: str = "") -> str:
        """Create email body for the user."""
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px; color: #333;">
            <h2 style="color: #2c3e50;">✅ Your Meeting with Peter Michael Gits is Confirmed!</h2>
            
            <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                <h3 style="margin-top: 0; color: #2e7d32;">{title}</h3>
                
                <div style="margin: 15px 0;">
                    <strong>📅 Date & Time:</strong><br>
                    {start_datetime.strftime('%A, %B %d, %Y')}<br>
                    {start_datetime.strftime('%I:%M %p')} - {end_datetime.strftime('%I:%M %p')} ({start_datetime.strftime('%Z')})
                </div>
                
                <div style="margin: 15px 0;">
                    <strong>👤 Meeting with:</strong> Peter Michael Gits<br>
                    <strong>📞 Peter's Phone:</strong> {settings.my_phone_number}<br>
                    <strong>📧 Peter's Email:</strong> {settings.my_email_address}
                    {f'<br><strong>🎥 Google Meet Link:</strong> <a href="{meet_link}" style="color: #1976d2; font-weight: bold;">{meet_link}</a>' if meet_link else ''}
                </div>
                
                {f'<div style="margin: 15px 0;"><strong>📝 Meeting Details:</strong><br>{description}</div>' if description else ''}
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h4 style="margin-top: 0; color: #856404;">📋 What's Next?</h4>
                <ul style="color: #856404; margin-bottom: 0;">
                    <li>Add this meeting to your calendar using the attached invitation file</li>
                    <li>Peter will reach out via the contact method you provided</li>
                    <li>If you need to reschedule, please contact Peter directly</li>
                </ul>
            </div>
            
            <p style="color: #6c757d; font-size: 14px;">
                Looking forward to your meeting! The calendar invitation is attached to this email.
            </p>
            
            <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                Sent by ChatCal.ai - Peter Michael Gits' AI Scheduling Assistant<br>
                Peter: {settings.my_phone_number} | {settings.my_email_address}
            </p>
        </body>
        </html>
        """
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML email to plain text."""
        import re
        
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text


# Global email service instance
email_service = EmailService()