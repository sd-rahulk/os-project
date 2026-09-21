from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import AdminUser

# PBKDF2 is available without a native extension on Windows and avoids
# relying on a brittle bcrypt backend in the packaged control center.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(username: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=get_settings().jwt_expire_minutes)
    return jwt.encode({"sub": username, "exp": expires}, get_settings().jwt_secret, algorithm="HS256")


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> AdminUser:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        username = jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=["HS256"]).get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc
    user = db.query(AdminUser).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user
