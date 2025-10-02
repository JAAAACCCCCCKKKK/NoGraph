from datetime import timedelta

import jwt
from django.http import JsonResponse
from django.utils import timezone

from NoGraph import settings


def create_jwt(pk,isop):
    payload = {
        'user_id': pk,
        'isop': isop,
        'exp':  timezone.now() + timedelta(seconds=settings.JWT_EXP),
        'iat':  timezone.now()
    }
    token = jwt.encode(payload, settings.JWT_KEY, algorithm=settings.JWT_ALG)
    return token

def check_jwt(tok):
    try:
        pl = jwt.decode(tok, settings.JWT_KEY, algorithms=[settings.JWT_ALG])
        return {'user_id': pl['user_id'], 'isop': pl['isop']}
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def healthcheck(request):
    return JsonResponse({'status': 'ok'},status=200)
