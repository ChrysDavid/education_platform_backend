from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class StandardUserRateThrottle(UserRateThrottle):
    """
    Limite le débit pour les utilisateurs authentifiés.
    """
    scope = 'standard_user'
    rate = '100/hour'

class BurstUserRateThrottle(UserRateThrottle):
    """
    Limite le débit pour des rafales rapides d'appels API.
    """
    scope = 'burst_user'
    rate = '30/minute'

class StandardAnonRateThrottle(AnonRateThrottle):
    """
    Limite le débit pour les utilisateurs anonymes.
    """
    scope = 'standard_anon'
    rate = '20/hour'

class BurstAnonRateThrottle(AnonRateThrottle):
    """
    Limite le débit pour des rafales rapides d'appels API anonymes.
    """
    scope = 'burst_anon'
    rate = '5/minute'

class VerificationRateThrottle(UserRateThrottle):
    """
    Limite le débit pour les requêtes de vérification.
    """
    scope = 'verification'
    rate = '5/day'

class AuthRateThrottle(AnonRateThrottle):
    """
    Limite le débit pour les tentatives d'authentification.
    """
    scope = 'auth'
    rate = '10/hour'