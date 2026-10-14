"""Bound request bodies, including chunked uploads, before application parsing."""
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self, app): self.app = app
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope.get('method') in {'GET', 'HEAD', 'OPTIONS'}:
            return await self.app(scope, receive, send)
        path = scope.get('path', '')
        maximum = 22*1024*1024 if path.endswith('/personal-documents') else 512*1024 if path.endswith('/photo') else 64*1024 if path.startswith('/api/account/') or path.endswith('/profile-draft') else 1024*1024
        length = dict(scope.get('headers', [])).get(b'content-length', b'')
        if length and (not length.isdigit() or int(length) > maximum):
            return await JSONResponse({'detail': {'code': 'request_too_large'}}, status_code=413)(scope, receive, send)
        total = 0
        async def bounded_receive():
            nonlocal total
            message = await receive()
            total += len(message.get('body', b''))
            if total > maximum: raise HTTPException(413, detail={'code': 'request_too_large'})
            return message
        await self.app(scope, bounded_receive, send)
