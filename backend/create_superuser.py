from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def init_db(db: Session):
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(
            username="admin",
            hashed_password=get_password_hash("admin"),
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        print("Superuser created")
    else:
        print("Superuser already exists")

if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
