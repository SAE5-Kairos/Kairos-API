from functools import wraps
from typing import Union
from django.http import JsonResponse
from enum import Enum
import jwt

SECRET = "jesuislaphraseextremementsecretedelamortquituenormalementpersonneestsenseletrouvemaisbononsaitjamais"

def method_awaited(method: Union[str, list]):
    def decorator_func(f):
        def warpper(*args, **kw):
            if args[0].method != method and type(method) != list or type(method) == list and args[
                0].method not in method:
                return JsonResponse({"error": f"method {args[0].method} found when {method} awaited"})
            return f(*args, **kw)

        return warpper

    return decorator_func


class Role(Enum):
    PROFESSEUR = "Professeur"
    ADMINISTRATEUR = "Administrateur"
    ETUDIANT = "Etudiant"


def jwt_required(roles: [Role] = None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return JsonResponse({'error': 'No token provided'}, status=401)
            try:
                payload = jwt.decode(token[7:], SECRET, algorithms=["HS256"])
                request.user = payload  # Attacher le payload au request pour y accéder dans la vue
                if roles and payload.get('status') not in [role.value for role in roles]:
                    return JsonResponse({'error': 'Not authorised'}, status=403)
            except jwt.ExpiredSignatureError:
                return JsonResponse({'error': 'Token expired'}, status=403)
            except jwt.PyJWTError as e:
                return JsonResponse({'error': 'Invalid token'}, status=403)
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
