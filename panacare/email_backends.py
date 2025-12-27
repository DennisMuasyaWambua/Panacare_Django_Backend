"""
Custom email backends with timeout settings to prevent worker timeouts
"""

from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
import socket


class TimeoutSMTPEmailBackend(EmailBackend):
    """
    SMTP backend with timeout support to prevent long-running email operations
    """
    
    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a
        new connection was required (True or False), with socket timeout applied.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False

        # If local_hostname is not specified, socket.getfqdn() gets used.
        # For performance, we use the cached FQDN for local_hostname.
        connection_params = {
            'local_hostname': getattr(settings, 'EMAIL_HOST_DOMAIN', None)
        }
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )
            
            # Apply socket timeout
            if hasattr(self.connection, 'sock') and self.connection.sock:
                timeout = getattr(settings, 'EMAIL_TIMEOUT', 30)
                self.connection.sock.settimeout(timeout)
            
            # TLS/SSL are mutually exclusive, so only attempt TLS over non-secure connections.
            if not self.use_ssl and self.use_tls:
                self.connection.starttls()
            if self.use_ssl:
                self.connection = self.connection_class(
                    self.host, self.port, **connection_params
                )
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except (socket.gaierror, socket.error, socket.timeout) as e:
            if not self.fail_silently:
                raise
            return False