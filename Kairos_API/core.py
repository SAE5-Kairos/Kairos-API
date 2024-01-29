from django.http import JsonResponse

def method_awaited(method:str):
    def decorator_func(f):
        def warpper(*args, **kw):
            if args[0].method != method:
                raise JsonResponse({"error": f"method {args[0].method} found when {method} awaited"})
            f(*args, **kw)
        return warpper
    return decorator_func
