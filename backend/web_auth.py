"""Sovereign WEB account authentication. User roles come from server-side records."""
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import hashlib
import os
import secrets
import smtplib
import uuid

import bcrypt
import jwt
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pathlib import Path
from pydantic import BaseModel, Field

COOKIE = "web_session"
_failed = {}

class LoginBody(BaseModel):
    identifier: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=1024)

class ResetRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=254)
    recovery_email: str = Field(min_length=3, max_length=254)

class ResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    new_password: str = Field(min_length=12, max_length=1024)

def _secret():
    value = (os.getenv("WEB_AUTH_SECRET") or "").strip()
    return value if len(value) >= 32 else None

def _hash_password(value):
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")

def _send_reset_email(to, username, token):
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if host not in {"smtp.gmail.com", "smtp-relay.gmail.com"} or not sender:
        raise RuntimeError("Recovery email is not configured")
    msg = EmailMessage()
    msg["Subject"] = "Restablecimiento de contraseña · OPORTUNIIA WEB"
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(f"Se solicitó restablecer la contraseña de {username}. Usa este enlace en 20 minutos:\n\n{os.getenv('WEB_PUBLIC_URL', '').rstrip('/')}/acceso?reset_token={token}\n\nSi no lo solicitaste, ignora este correo.")
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.starttls()
        user, password = os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD")
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)

def register_web_auth(app: FastAPI, db):
    async def get_session(token):
        secret = _secret()
        if not secret or not token:
            return None
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None
        account = await db.web_auth_users.find_one({"id": payload.get("sub"), "is_active": True}, {"_id": 0})
        if not account or payload.get("tv") != account.get("token_version", 0):
            return None
        return account

    @app.on_event("startup")
    async def _auth_indexes_and_bootstrap():
        await db.web_auth_users.create_index("username_norm", unique=True)
        await db.web_auth_users.create_index("email_norm")
        await db.web_auth_resets.create_index("token_hash", unique=True)
        await db.web_auth_resets.create_index("expires_at", expireAfterSeconds=0)
        seeds = [
            ("WEB_MASTER", "ADMIN"),
            ("WEB_STANDARD", "USER"),
        ]
        for prefix, role in seeds:
            username = (os.getenv(prefix + "_USERNAME") or "").strip()
            email = (os.getenv(prefix + "_RECOVERY_EMAIL") or "").strip().lower()
            password = os.getenv(prefix + "_PASSWORD")
            if not (username and email and password):
                continue
            existing = await db.web_auth_users.find_one({"username_norm": username.casefold()})
            if existing:
                continue
            doc = {
                "id": str(uuid.uuid4()), "username": username,
                "username_norm": username.casefold(), "email": email,
                "email_norm": email, "role": role,
                "password_hash": _hash_password(password), "token_version": 0,
                "must_change_password": True,
                "temporary_password_expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
                "is_active": True, "created_at": datetime.now(timezone.utc),
            }
            await db.web_auth_users.insert_one(doc)

    @app.middleware("http")
    async def _protect_private_web_area(request: Request, call_next):
        if request.url.path == "/mi-oportuniia" or request.url.path.startswith("/mi-oportuniia/"):
            account = await get_session(request.cookies.get(COOKIE))
            if not account:
                return RedirectResponse("/acceso?next=" + request.url.path, status_code=303)
            if account.get("must_change_password"):
                return RedirectResponse("/cuenta/contrasena", status_code=303)
            request.state.web_user = {"id": account["id"], "username": account["username"], "role": account["role"]}
        return await call_next(request)

    @app.post("/api/auth/login")
    async def login(body: LoginBody, request: Request):
        secret = _secret()
        if not secret:
            return JSONResponse({"detail": "Acceso no configurado todavía"}, status_code=503)
        ip = request.client.host if request.client else "unknown"
        now = datetime.now(timezone.utc).timestamp()
        fails = [t for t in _failed.get(ip, []) if now - t < 600]
        if len(fails) >= 10:
            return JSONResponse({"detail": "Demasiados intentos. Prueba más tarde."}, status_code=429)
        ident = body.identifier.strip()
        rows = await db.web_auth_users.find({"$or": [{"username_norm": ident.casefold()}, {"email_norm": ident.lower()}], "is_active": True}, {"_id": 0}).limit(2).to_list(2)
        account = rows[0] if len(rows) == 1 else None
        valid = False
        if account:
            try:
                valid = bcrypt.checkpw(body.password.encode("utf-8"), account["password_hash"].encode("ascii"))
            except (ValueError, KeyError):
                valid = False
        if not valid:
            _failed[ip] = fails + [now]
            return JSONResponse({"detail": "Usuario/correo o contraseña incorrectos"}, status_code=401)
        from local_accounts import check_initial_expiry
        check_initial_expiry(account)
        _failed.pop(ip, None)
        token = jwt.encode({"sub": account["id"], "tv": account["token_version"], "exp": datetime.now(timezone.utc) + timedelta(hours=8)}, secret, algorithm="HS256")
        response = JSONResponse({"ok": True, "user": {"username": account["username"], "role": account["role"], "must_change_password": account.get("must_change_password", False)}})
        response.set_cookie(COOKIE, token, httponly=True, secure=True, samesite="lax", max_age=28800, path="/")
        return response

    @app.post("/api/auth/logout")
    async def logout():
        response = JSONResponse({"ok": True})
        response.delete_cookie(COOKIE, path="/")
        return response

    @app.get("/api/auth/me")
    async def me(request: Request):
        account = await get_session(request.cookies.get(COOKIE))
        if not account:
            return JSONResponse({"detail": "Sesión no válida"}, status_code=401)
        return {"username": account["username"], "role": account["role"]}

    @app.post("/api/auth/password-reset/request")
    async def request_reset(body: ResetRequest, request: Request):
        ip = request.client.host if request.client else "unknown"
        now = datetime.now(timezone.utc).timestamp()
        recent = [t for t in _failed.get("reset:" + ip, []) if now - t < 900]
        if len(recent) >= 5:
            return {"ok": True, "message": "Si los datos corresponden a una cuenta, enviaremos instrucciones al correo de recuperación."}
        _failed["reset:" + ip] = recent + [now]
        ident = body.identifier.strip()
        rows = await db.web_auth_users.find({"$or": [{"username_norm": ident.casefold()}, {"email_norm": ident.lower()}], "email_norm": body.recovery_email.strip().lower(), "is_active": True}, {"_id": 0}).limit(2).to_list(2)
        # Always return the same response to avoid account enumeration.
        if len(rows) == 1:
            token = secrets.token_urlsafe(32)
            await db.web_auth_resets.insert_one({
                "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                "user_id": rows[0]["id"],
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=20),
            })
            try:
                _send_reset_email(rows[0]["email"], rows[0]["username"], token)
            except Exception:
                await db.web_auth_resets.delete_one({"token_hash": hashlib.sha256(token.encode()).hexdigest()})
        return {"ok": True, "message": "Si los datos corresponden a una cuenta, enviaremos instrucciones al correo de recuperación."}

    @app.post("/api/auth/password-reset/confirm")
    async def confirm_reset(body: ResetConfirm):
        token_hash = hashlib.sha256(body.token.encode()).hexdigest()
        from local_accounts import password_valid
        password_valid(body.new_password)
        reset = await db.web_auth_resets.find_one_and_delete({"token_hash": token_hash, "expires_at": {"$gt": datetime.now(timezone.utc)}})
        if not reset:
            return JSONResponse({"detail": "Enlace inválido o caducado"}, status_code=400)
        await db.web_auth_users.update_one({"id": reset["user_id"], "is_active": True}, {"$set": {"password_hash": _hash_password(body.new_password), "must_change_password": False}, "$unset": {"temporary_password_expires_at": ""}, "$inc": {"token_version": 1}})
        await db.web_auth_resets.delete_one({"token_hash": token_hash})
        return {"ok": True}



    # Cookie identity and account persistence stay local to WEB.
    from local_accounts import build_accounts_router, ensure_account_indexes, require_password_change
    class AccountsDB:
        users = db.web_auth_users
        def __getattr__(self, name):
            return getattr(db, name)
    account_db = AccountsDB()
    async def account_user(request: Request):
        account = await get_session(request.cookies.get(COOKIE))
        if not account:
            raise HTTPException(401, "Sesión no válida")
        origin = request.headers.get("origin")
        allowed = {str(request.base_url).rstrip("/"), os.environ.get("WEB_PUBLIC_URL", "").rstrip("/")}
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin not in allowed:
            raise HTTPException(403, "Origen no permitido")
        require_password_change(account, request.url.path)
        account.pop("password_hash", None)
        return account
    def verify(plain, hashed):
        try:
            return bcrypt.checkpw(plain.encode(), hashed.encode())
        except (ValueError, TypeError):
            return False
    app.include_router(build_accounts_router(account_db, account_user, _hash_password, verify,
        roles=("ADMIN", "USER"), admin_role="ADMIN", active_field="is_active"))
    @app.on_event("startup")
    async def account_indexes():
        await ensure_account_indexes(account_db)
    @app.get("/cuenta/{page}", response_class=HTMLResponse)
    async def account_page(page: str):
        if page not in {"usuarios", "contrasena", "recuperar"}:
            raise HTTPException(404, "Página no encontrada")
        content = Path(__file__).parent.parent / "frontend" / "public" / "cuenta.html"
        return HTMLResponse(content.read_text(encoding="utf-8"))
