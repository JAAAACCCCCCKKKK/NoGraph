from datetime import timedelta

import jwt
from django.http import JsonResponse
from django.utils import timezone

from NoGraph import settings


def create_jwt(pk):
    payload = {
        'user_id': pk,
        'exp':  timezone.now() + timedelta(seconds=settings.JWT_EXP),
        'iat':  timezone.now()
    }
    token = jwt.encode(payload, settings.JWT_KEY, algorithm=settings.JWT_ALG)
    return token

def check_jwt(tok):
    try:
        pl = jwt.decode(tok, settings.JWT_KEY, algorithms=[settings.JWT_ALG])
        return pl['user_id']
    except jwt.ExpiredSignatureError:
        return "expd"
    except jwt.InvalidTokenError:
        return "invt"

def healthcheck(request):
    return JsonResponse({'status': 'ok'},status=200)
