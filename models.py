import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import BigInteger, String, Text, Numeric, Boolean, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


# --- ENUM TURLARI ---

class ProjectStatus(str, enum.Enum):
    # Muzokara bosqichi
    PENDING = "pending"                  # Yangi tushgan, ko'rib chiqilmoqda
    PRICING = "pricing"                  # Narxlanmoqda (AI/Admin)
    NEGOTIATING = "negotiating"          # Mijoz narx taklif qildi (savdolashuv)
    WAITING_PAYMENT = "waiting_payment"  # 20% to'lov kutilmoqda
    PAYMENT_CHECKING = "payment_checking"# Chek tekshirilmoqda
    
    # Ishlash bosqichi (Siz aytgan statuslar)
    BUILDING = "building"                # Ishlanmoqda
    UPDATING = "updating"                # Yangilanmoqda
    READY = "ready"                      # Topshirishga tayyor
    ACTIVE = "active"                    # Topshirilgan va aktiv
    CANCELLED = "cancelled"              # Bekor qilingan


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# --- MODELLAR ---

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="uz", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Loyiha ma'lumotlari
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    about: Mapped[str] = mapped_column(Text, nullable=False)
    template_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Frontend shablon
    type: Mapped[str] = mapped_column(String(50), nullable=False)   # startup, landing, project
    build: Mapped[str] = mapped_column(String(50), nullable=False)  # mobile app, web site, telegram bot, allinone
    deadline: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    warranty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Narx va Savdolashuv
    price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)             # Yakuniy kelishilgan narx
    user_offered_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)# User taklif qilgan narx

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False), 
        default=ProjectStatus.PENDING, 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="project", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    receipt_file_id: Mapped[str] = mapped_column(String(255), nullable=False) # Telegram chek rasmi ID
    is_part: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # True = 20% advance, False = Full
    
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, native_enum=False), 
        default=TransactionStatus.PENDING, 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    project: Mapped["Project"] = relationship("Project", back_populates="transactions")