# Email Setup Guide for ChatCal.ai

## Overview

ChatCal.ai includes full email integration with Gmail SMTP to automatically send calendar invitations to both the user and Peter for confirmed bookings. This guide covers the complete setup process.

## Gmail App Password Setup

### Step 1: Enable 2-Factor Authentication

1. Go to your Google Account settings
2. Navigate to Security > 2-Step Verification
3. Enable 2-Factor Authentication if not already enabled

### Step 2: Generate App Password

1. In Google Account settings, go to Security
2. Under "2-Step Verification", click on "App passwords"
3. Select "Mail" and "Other (Custom name)"
4. Enter "ChatCal.ai" as the custom name
5. Click "Generate"
6. Copy the 16-character app password (format: xxxx xxxx xxxx xxxx)

### Step 3: Configure Environment Variables

Add to your `.env` file:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
```

## Email Functionality

### Automatic Email Invitations

When a booking is confirmed, the system automatically:

1. **Sends to User**: Calendar invitation with meeting details
2. **Sends to Peter**: Notification with user information and meeting details
3. **Includes .ics Attachment**: Calendar file for easy import
4. **Contains Google Meet Link**: For virtual meetings

### Email Template Features

- **Professional HTML formatting**
- **Meeting details**: Date, time, duration, attendees
- **Contact information**: User's email and phone
- **Meeting type**: Google Meet or in-person
- **Custom meeting ID**: For easy reference and cancellation

### Sample Email Content

```
Subject: Meeting Confirmation - Jennifer Wilson - Tomorrow 2:15 PM

Dear Jennifer,

Your meeting with Peter Michael Gits has been confirmed!

Meeting Details:
• Date: Tomorrow
• Time: 2:15 PM
• Duration: 45 minutes
• Type: Google Meet Consultation
• Meeting ID: 0801-1415-45m

Google Meet Link: [Included in calendar invitation]

Contact: pgits.job@gmail.com | 555-123-4567

Best regards,
ChatCal.ai
```

## Testing Email Functionality

### Development Mode

Set `TESTING_MODE=true` in your `.env` file to:
- Skip email validation for Peter's address
- Enable detailed logging of email sending process
- Allow testing without affecting production emails

### Production Testing

1. Use the production test script:
```bash
python test_production_booking.py
```

2. Check Docker logs for email activity:
```bash
docker logs chatcal-api --tail=20
```

3. Look for these log entries:
```
✅ Email invitation sent to user@example.com
✅ Email invitation sent to pgits.job@gmail.com
```

## Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Verify app password is correct (16 characters, no spaces)
   - Ensure 2FA is enabled on Gmail account
   - Check SMTP_USERNAME matches the Gmail account

2. **"Connection refused"**
   - Verify SMTP server and port settings
   - Check firewall/network restrictions
   - Ensure Gmail SMTP is enabled

3. **Emails not being sent**
   - Check that tool invocation is working (see agent.py logs)
   - Verify SMTP configuration in environment variables
   - Test with simple email test script

### Debug Commands

```bash
# Check SMTP configuration
docker logs chatcal-api | grep -i smtp

# Monitor email sending
docker logs chatcal-api --follow | grep -i email

# Test complete booking flow
python test_production_booking.py
```

## Production Deployment

### Security Considerations

1. **Never commit SMTP credentials** to version control
2. **Use environment-specific configurations**
3. **Rotate app passwords periodically**
4. **Monitor email usage** to prevent abuse

### Email Rate Limits

Gmail SMTP has rate limits:
- **500 emails per day** for regular Gmail accounts
- **2000 emails per day** for Google Workspace accounts
- **100 emails per hour** burst limit

For high-volume usage, consider:
- Google Workspace account
- Dedicated email service (SendGrid, Mailgun)
- Multiple SMTP providers for redundancy

## Advanced Configuration

### Custom Email Templates

Email templates are defined in:
- `app/core/tools.py` - Email content generation
- `app/core/email_service.py` - SMTP handling

### Multiple SMTP Providers

To add backup email providers, modify `email_service.py`:

```python
SMTP_PROVIDERS = [
    {
        'server': 'smtp.gmail.com',
        'port': 587,
        'username': os.getenv('SMTP_USERNAME'),
        'password': os.getenv('SMTP_PASSWORD')
    },
    {
        'server': 'smtp.sendgrid.net',
        'port': 587,
        'username': 'apikey',
        'password': os.getenv('SENDGRID_API_KEY')
    }
]
```

## Integration with Calendar Tools

The email system integrates seamlessly with the calendar booking tools:

1. **create_appointment** tool triggers email sending
2. **cancel_appointment** tool sends cancellation emails
3. **Email validation** ensures deliverability
4. **Error handling** provides graceful fallback

This integration ensures that every confirmed booking results in proper email notifications to all parties.