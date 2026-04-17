"""
Enhanced Email Service with QR Code Support
Supports inline QR codes and attachments in email templates
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, Header
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import base64
from config.settings import (
    EMAIL_PROVIDER, SENDGRID_API_KEY, SENDGRID_FROM_EMAIL,
    GMAIL_USER, GMAIL_APP_PASSWORD
)
from scripts.utils.logger import logger

def create_shift_reminder_email_with_qr(
    volunteer_name: str, 
    shift_name: str, 
    shift_date: str, 
    shift_time: str, 
    location: str, 
    qr_code_path: str = None,
    cid_image: str = "shift_qr",
    special_instructions: str = None
) -> tuple:
    """
    Create HTML email for shift reminder with embedded QR code
    
    Args:
        volunteer_name: Volunteer's name
        shift_name: Name of the shift
        shift_date: Shift date (YYYY-MM-DD)
        shift_time: Shift time (HH:MM)
        location: Shift location
        qr_code_path: Path to QR code image file (None = no QR code)
        cid_image: Content-ID for embedded image (used in HTML)
        special_instructions: Optional special instructions
    
    Returns:
        tuple: (html_content: str, text_content: str, qr_path_for_attachment: str)
    """
    
    qr_img_html = ""
    if qr_code_path and Path(qr_code_path).exists():
        qr_img_html = f"""
        <div style="text-align: center; margin: 20px 0;">
            <p style="font-weight: bold; color: #0066cc; margin-bottom: 10px;">
                 Quick Check-In: Scan this QR code when you arrive
            </p>
            <img src="cid:{cid_image}" alt="Check-in QR Code" style="width: 250px; height: 250px; border: 2px solid #ddd; border-radius: 8px; padding: 10px; background: white;">
        </div>
        """
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 0; border-radius: 0 0 5px 5px; }}
            .shift-details {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; border-radius: 4px; }}
            .shift-details strong {{ color: #0066cc; }}
            .shift-details p {{ margin: 8px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; margin-top: 20px; border-top: 1px solid #ddd; }}
            .button {{ background-color: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }}
            .important {{ background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; margin: 15px 0; color: #856404; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1> Shift Reminder</h1>
                <p>You have an upcoming volunteering shift!</p>
            </div>
            <div class="content">
                <p>Hi {volunteer_name},</p>
                <p>This is a friendly reminder about your upcoming volunteer shift:</p>
                
                <div class="shift-details">
                    <p><strong> Shift Name:</strong> {shift_name}</p>
                    <p><strong> Date:</strong> {shift_date}</p>
                    <p><strong> Time:</strong> {shift_time}</p>
                    <p><strong> Location:</strong> {location}</p>
                    {f'<p><strong> Special Instructions:</strong> {special_instructions}</p>' if special_instructions else ''}
                </div>
                
                {qr_img_html}
                
                <div class="important">
                    <strong>Important:</strong> Please arrive 10 minutes early to check in. If you can no longer make it, please notify us ASAP so we can arrange a replacement.
                </div>
                
                <p>Thank you for your commitment to our community! Your volunteer work makes a real difference.</p>
                
                <p>Questions? reply to this email or contact the shift coordinator.</p>
                
                <p>Best regards,<br>Food Bank Volunteer Coordination Team</p>
            </div>
            <div class="footer">
                <p>This is an automated reminder. Please do not forward this email as it contains unique QR codes.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    SHIFT REMINDER
    
    Hi {volunteer_name},
    
    This is a friendly reminder about your upcoming volunteer shift:
    
    Shift Name: {shift_name}
    Date: {shift_date}
    Time: {shift_time}
    Location: {location}
    {f'Special Instructions: {special_instructions}' if special_instructions else ''}
    
    Please arrive 10 minutes early to check in.
    If you cannot make it, please notify us as soon as possible.
    
    Thank you for your commitment!
    Food Bank Volunteer Coordination Team
    """
    
    return html_content, text_content, qr_code_path


def send_email_with_qr_attachment(to_email: str, subject: str, html_content: str, 
                                  qr_code_path: str = None, text_content: str = None) -> tuple:
    """
    Send email via configured provider with QR code attachment and inline image
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body (can reference cid:shift_qr for inline image)
        qr_code_path: Path to QR code image file
        text_content: Plain text fallback
    
    Returns:
        tuple: (success: bool, message_id: str or error: str)
    """
    try:
        if EMAIL_PROVIDER == 'sendgrid':
            return send_via_sendgrid_with_qr(to_email, subject, html_content, qr_code_path, text_content)
        elif EMAIL_PROVIDER == 'gmail':
            return send_via_gmail_with_qr(to_email, subject, html_content, qr_code_path, text_content)
        else:
            logger.error(f"Unknown email provider: {EMAIL_PROVIDER}")
            return False, "Invalid email provider configuration"
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False, str(e)


def send_via_sendgrid_with_qr(to_email: str, subject: str, html_content: str, 
                              qr_code_path: str = None, text_content: str = None) -> tuple:
    """Send email via SendGrid with QR code attachment"""
    try:
        message = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        # Add plain text version if provided
        if text_content:
            message.plain_text_content = text_content
        
        # Attach QR code if provided
        if qr_code_path and Path(qr_code_path).exists():
            with open(qr_code_path, 'rb') as attachment:
                data = base64.b64encode(attachment.read()).decode()
                
                # Add as attachment
                att = Attachment(
                    FileContent(data),
                    FileName('shift_qr_code.png'),
                    FileType('image/png'),
                    Disposition('attachment')
                )
                message.attachment = att
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f" Email sent to {to_email} via SendGrid with QR code")
        return True, response.headers.get('X-Message-Id', 'message-sent')
        
    except Exception as e:
        logger.error(f" SendGrid error: {e}")
        return False, str(e)


def send_via_gmail_with_qr(to_email: str, subject: str, html_content: str, 
                           qr_code_path: str = None, text_content: str = None) -> tuple:
    """Send email via Gmail with QR code attachment"""
    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        
        # Create alternative part for plain text and HTML
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
        # Add plain text
        if text_content:
            part_text = MIMEText(text_content, 'plain')
            msg_alternative.attach(part_text)
        
        # Add HTML
        part_html = MIMEText(html_content, 'html')
        msg_alternative.attach(part_html)
        
        # Attach QR code image
        if qr_code_path and Path(qr_code_path).exists():
            with open(qr_code_path, 'rb') as attachment:
                img = MIMEImage(attachment.read(), 'png')
                img.add_header('Content-Disposition', 'inline', filename='shift_qr_code.png')
                img.add_header('Content-ID', '<shift_qr>')
                msg.attach(img)
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f" Email sent to {to_email} via Gmail with QR code")
        return True, "gmail-sent"
        
    except Exception as e:
        logger.error(f" Gmail error: {e}")
        return False, str(e)


# For backwards compatibility, re-export the original email_service functions
def send_reminder_email_to_volunteer(volunteer_name: str, volunteer_email: str, shift_name: str,
                                     shift_date: str, shift_time: str, location: str, 
                                     qr_code_path: str = None, special_instructions: str = None) -> tuple:
    """
    High-level function to send shift reminders with QR codes
    
    Returns:
        tuple: (success: bool, message_id: str or error: str)
    """
    try:
        # Create email content with QR code
        html_content, text_content, _ = create_shift_reminder_email_with_qr(
            volunteer_name=volunteer_name,
            shift_name=shift_name,
            shift_date=shift_date,
            shift_time=shift_time,
            location=location,
            qr_code_path=qr_code_path,
            special_instructions=special_instructions
        )
        
        # Send email with QR code attachment
        success, message_id = send_email_with_qr_attachment(
            to_email=volunteer_email,
            subject=f"Reminder: {shift_name} on {shift_date}",
            html_content=html_content,
            qr_code_path=qr_code_path,
            text_content=text_content
        )
        
        return success, message_id
    
    except Exception as e:
        logger.error(f"Error sending reminder email: {e}")
        return False, str(e)


if __name__ == "__main__":
    # Test email generation
    html, text, qr_path = create_shift_reminder_email_with_qr(
        "John Doe",
        "Food Bank - Morning Shift",
        "2024-03-20",
        "08:00",
        "Main Street Food Bank",
        qr_code_path=None,
        special_instructions="Bring comfortable shoes"
    )
    print(" Email template generated successfully")
