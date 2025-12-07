from datetime import datetime, timedelta
import jwt
import hashlib
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import argon2
from frontend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")


###################### PASSWORD ######################
def preprocess(password: str) -> str:
    sha256 = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return sha256  # Always exactly 64 chars, safe for bcrypt


def hash_pwd(password: str) -> str:
    return argon2.hash(password)


def verify_pwd(password: str, hashed: str) -> bool:
    return argon2.verify(password, hashed)


###################### TOKEN CREATION ######################
def create_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


###################### TOKEN VERIFY ######################
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
