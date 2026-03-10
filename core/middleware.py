"""
Security middleware for Cinema Project
- SecurityHeadersMiddleware: Adds Content-Security-Policy and other security headers
- BruteForceProtectionMiddleware: Rate-limits login attempts and sensitive endpoints
"""
import time
import logging
from collections import defaultdict
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('core.security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds additional security headers to every response:
    - Content-Security-Policy (CSP)
    - Permissions-Policy
    - X-Content-Type-Options
    """
    
    def process_response(self, request, response):
        
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "font-src 'self' https://cdn.jsdelivr.net",
            "img-src 'self' data: https://m.media-amazon.com",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=()'
        )
        
        
        response['X-Content-Type-Options'] = 'nosniff'
        
        
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Rate-limits requests to sensitive endpoints (login, ticket purchase).
    Tracks by IP address and blocks after too many attempts.
    """
    
    
    _request_log = defaultdict(list)
    
    
    RATE_LIMIT_WINDOW = 60          
    MAX_LOGIN_ATTEMPTS = 10         
    MAX_PURCHASE_ATTEMPTS = 20      
    BLOCK_DURATION = 300            
    
    
    _blocked_ips = {}
    
    PROTECTED_PATHS = {
        '/accounts/login/': 'login',
        '/accounts/signup/': 'login',
    }
    
    def _get_client_ip(self, request):
        """Extract real client IP, considering proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    def _cleanup_old_entries(self, ip):
        """Remove entries older than the rate limit window"""
        cutoff = time.time() - self.RATE_LIMIT_WINDOW
        self._request_log[ip] = [
            (ts, path) for ts, path in self._request_log[ip]
            if ts > cutoff
        ]
    
    def process_request(self, request):
        
        if request.method != 'POST':
            return None
        
        ip = self._get_client_ip(request)
        now = time.time()
        
        
        if ip in self._blocked_ips:
            if now < self._blocked_ips[ip]:
                remaining = int(self._blocked_ips[ip] - now)
                logger.warning(
                    f"Blocked IP {ip} attempted access to {request.path}. "
                    f"Block remaining: {remaining}s"
                )
                return HttpResponseForbidden(
                    f"Túl sok kérés. Próbálja újra {remaining} másodperc múlva."
                )
            else:
                del self._blocked_ips[ip]
        
        
        path = request.path
        is_login = any(path.startswith(p) for p in self.PROTECTED_PATHS)
        is_purchase = '/buy/' in path or '/sell/' in path
        
        if not (is_login or is_purchase):
            return None
        
        
        self._request_log[ip].append((now, path))
        self._cleanup_old_entries(ip)
        
        
        recent_count = len(self._request_log[ip])
        max_allowed = self.MAX_LOGIN_ATTEMPTS if is_login else self.MAX_PURCHASE_ATTEMPTS
        
        if recent_count > max_allowed:
            self._blocked_ips[ip] = now + self.BLOCK_DURATION
            logger.warning(
                f"IP {ip} blocked for {self.BLOCK_DURATION}s after "
                f"{recent_count} requests to {path}"
            )
            return HttpResponseForbidden(
                "Túl sok kérés. Az Ön IP címe ideiglenesen blokkolva lett. "
                "Próbálja újra 5 perc múlva."
            )
        
        return None
