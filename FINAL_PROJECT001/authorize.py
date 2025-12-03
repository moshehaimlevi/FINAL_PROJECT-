from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt
import jwt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

###################### PASSWORD ######################
def hash_pwd(password: str) -> str:
    return bcrypt.hash(password)

def verify_pwd(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)

###################### TOKEN CREATING ######################
def create_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

###################### VERIFYING THE TOKEN ######################

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
