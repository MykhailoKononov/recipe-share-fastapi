from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.database.models import User, Role
import settings
from fastapi.security import OAuth2PasswordBearer


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/sign-in")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return credentials_exception
        user = await db.execute(select(User).filter(User.email == email, User.is_active == True))
        user = user.scalar()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception
