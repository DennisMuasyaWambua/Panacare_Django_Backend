"""
Custom email backends for robust email sending with fallbacks
"""
import logging
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from django.conf import settings

logger = logging.getLogger(__name__)

class FallbackEmailBackend:
    """
    Email backend that tries SMTP first, then falls back to console logging
    """
    
    def __init__(self, **kwargs):
        self.smtp_backend = SMTPBackend(**kwargs)
        self.console_backend = ConsoleBackend(**kwargs)
        
    def send_messages(self, email_messages):
        """
        Try to send via SMTP, fallback to console if it fails
        """
        if not email_messages:
            return 0
            
        # Try SMTP first with timeout protection
        try:
            import signal
            
            def timeout_handler(signum, frame):
                raise Exception("SMTP timeout after 10 seconds")
            
            # Set a 10-second timeout for SMTP
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)
            
            try:
                result = self.smtp_backend.send_messages(email_messages)
                signal.alarm(0)  # Cancel alarm
                
                if result > 0:
                    logger.info(f"Successfully sent {result} emails via SMTP")
                    return result
                else:
                    logger.warning("SMTP backend returned 0, trying fallback")
                    raise Exception("SMTP backend failed to send messages")
                    
            finally:
                signal.alarm(0)  # Ensure alarm is cancelled
                
        except Exception as e:
            logger.error(f"SMTP email sending failed: {str(e)}")
            logger.info("Falling back to console email backend")
            
            # Fallback to console backend
            try:
                # Log the email details for debugging
                for message in email_messages:
                    logger.info(f"FALLBACK EMAIL - To: {message.to}, Subject: {message.subject}")
                    logger.info(f"FALLBACK EMAIL - From: {message.from_email}")
                    logger.info(f"FALLBACK EMAIL - Body: {message.body[:200]}...")
                
                # Use console backend as fallback
                result = self.console_backend.send_messages(email_messages)
                logger.info(f"Fallback console backend processed {result} messages")
                return result
                
            except Exception as console_error:
                logger.error(f"Console email backend also failed: {str(console_error)}")
                return 0
    
    def open(self):
        """Open connection - delegate to SMTP backend"""
        try:
            return self.smtp_backend.open()
        except:
            return True  # Console backend doesn't need opening
    
    def close(self):
        """Close connection - delegate to SMTP backend"""
        try:
            return self.smtp_backend.close()
        except:
            return True  # Console backend doesn't need closing