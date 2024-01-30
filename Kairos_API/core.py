from django.http import JsonResponse


def method_awaited(method: str or list):
    def decorator_func(f):
        def warpper(*args, **kw):
            if args[0].method != method and type(method) != list or type(method) == list and args[0].method not in method:
                return JsonResponse({"error": f"method {args[0].method} found when {method} awaited"})
            return f(*args, **kw)

        return warpper

    return decorator_func
