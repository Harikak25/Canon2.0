from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, LargeBinary, TIMESTAMP, text
from uuid import UUID, uuid4
from datetime import datetime

class Base(DeclarativeBase): pass

class EmailRecord(Base):
    __tablename__ = "emails"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email_id: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
