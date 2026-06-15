import uuid

from sqlalchemy import (
    Column,
    Text,
    DateTime,
    text
)

from sqlalchemy.dialects.postgresql import (
    UUID
)

from sqlalchemy.orm import (
    declarative_base
)


Base = declarative_base()


class Task(Base):

    __tablename__ = "tasks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    project_id = Column(
        UUID(as_uuid=True)
    )

    title = Column(
        Text,
        nullable=False
    )

    description = Column(
        Text
    )

    status = Column(
        Text,
        nullable=False,
        server_default=text("'pending'")
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )
