import os
from django.conf import settings


def validate_hls_access(movie_id, resolution, user=None):
    """
    Validiere HLS-Zugriff (für spätere Erweiterungen wie Authentifizierung)
    """
    # Hier könntest du später Benutzer-Authentifizierung hinzufügen
    # z.B. Premium-Nutzer für 1080p

    allowed_resolutions = ["120p", "360p", "720p", "1080p"]
    if resolution not in allowed_resolutions:
        return False

    # Weitere Validierungen...
    return True
