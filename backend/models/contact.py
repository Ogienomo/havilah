from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy import text

from sqlalchemy.dialects.postgresql import UUID

from backend.models.memory import Base


class Contact(Base):

    __tablename__ = "contacts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    organization_id = Column(
        UUID(as_uuid=True)
    )

    first_name = Column(
        Text,
        nullable=False
    )

    last_name = Column(Text)

    email = Column(Text)

    phone = Column(Text)

    relationship_type = Column(Text)

    relationship_status = Column(
        Text,
        default="active"
    )

    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()")
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()")
    )
