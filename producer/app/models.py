from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, LargeBinary, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime

class Base(DeclarativeBase): pass

class EmailRecord(Base):
    __tablename__ = "emails"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_data: Mapped[bytes | None] = mapped_column(LargeBinary(length=10 * 1024 * 1024), nullable=True)
    submitted_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
