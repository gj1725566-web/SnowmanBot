from sqlalchemy import create_engine, Column, Integer, String, Numeric, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///shop.db")
# Railway PostgreSQL requires handling the postgres:// prefix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    image_file_id = Column(String(300))  # Telegram file_id, no need to store images yourself
    description = Column(Text, default="")

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)

def get_setting(key, default=""):
    s = SessionLocal()
    row = s.query(Setting).filter_by(key=key).first()
    s.close()
    return row.value if row else default

def set_setting(key, value):
    s = SessionLocal()
    row = s.query(Setting).filter_by(key=key).first()
    if row:
        row.value = value
    else:
        s.add(Setting(key=key, value=value))
    s.commit()
    s.close()

def init_db():
    Base.metadata.create_all(engine)
