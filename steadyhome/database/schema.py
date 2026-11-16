from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

Base = declarative_base()

class Borrower(Base):
    __tablename__ = 'borrowers'

    borrower_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    date_of_birth = Column(String(20), nullable=False)  # YYYY-MM-DD
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default='ACTIVE')  # ACTIVE, BLOCKED
    address = Column(String(200), nullable=True)
    created_at = Column(String(30), default=lambda: datetime.now(timezone.utc).isoformat())

    loans = relationship("Loan", back_populates="borrower", cascade="all, delete-orphan")


class Loan(Base):
    __tablename__ = 'loans'

    loan_id = Column(String(50), primary_key=True, index=True)
    borrower_id = Column(String(50), ForeignKey('borrowers.borrower_id'), nullable=False, index=True)
    loan_amount = Column(Float, nullable=False)
    loan_status = Column(String(20), nullable=False, default='ACTIVE')  # ACTIVE, CLOSED, DEFAULT, UNKNOWN
    loan_tenure_months = Column(Integer, nullable=False, default=240)
    interest_rate = Column(Float, nullable=False, default=8.5)
    emi_amount = Column(Float, nullable=False)
    next_due_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    sanction_date = Column(String(20), nullable=False)

    borrower = relationship("Borrower", back_populates="loans")
    emis = relationship("EMI", back_populates="loan", cascade="all, delete-orphan")


class EMI(Base):
    __tablename__ = 'emis'

    emi_id = Column(String(50), primary_key=True, index=True)
    loan_id = Column(String(50), ForeignKey('loans.loan_id'), nullable=False, index=True)
    borrower_id = Column(String(50), nullable=False, index=True)
    emi_amount = Column(Float, nullable=False)
    due_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    payment_status = Column(String(20), nullable=False, default='PENDING')  # PAID, PENDING, OVERDUE
    payment_mode = Column(String(50), nullable=False, default='AutoDebit')  # AutoDebit, NetPay, Branch Cash Desk, KiteWallet
    days_overdue = Column(Integer, default=0)
    late_fee = Column(Float, default=0.0)
    paid_date = Column(String(20), nullable=True)

    loan = relationship("Loan", back_populates="emis")
    payments = relationship("Payment", back_populates="emi", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = 'payments'

    payment_id = Column(String(50), primary_key=True, index=True)
    emi_id = Column(String(50), ForeignKey('emis.emi_id'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_date = Column(String(20), nullable=False)
    payment_mode = Column(String(50), nullable=False)
    payment_status = Column(String(20), nullable=False, default='SUCCESS')  # SUCCESS, PENDING, FAILED, REJECTED
    reference_no = Column(String(100), nullable=False)
    notes = Column(String(200), nullable=True)

    emi = relationship("EMI", back_populates="payments")


class Escalation(Base):
    __tablename__ = 'escalations'

    escalation_id = Column(String(50), primary_key=True, index=True)
    borrower_id = Column(String(50), nullable=True, index=True)
    intent = Column(String(50), nullable=False)
    reason = Column(String(200), nullable=False)
    payment_mode = Column(String(50), nullable=True)
    conversation_summary = Column(Text, nullable=False)
    transfer_status = Column(String(30), nullable=False, default='INITIATED')  # INITIATED, ASSIGNED, RESOLVED
    timestamp = Column(String(30), nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())


class InteractionLog(Base):
    __tablename__ = 'interaction_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=False, index=True)
    borrower_id = Column(String(50), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)
    agent_name = Column(String(50), nullable=False)
    details = Column(Text, nullable=False)
    timestamp = Column(String(30), nullable=False, default=lambda: datetime.now(timezone.utc).isoformat())


def get_db_path():
    db_path = os.getenv("DATABASE_PATH")
    if not db_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "steadyhome.db")
    return db_path

def get_engine(db_path=None):
    if not db_path:
        db_path = get_db_path()
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine

