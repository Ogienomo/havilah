from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import DateTime
from sqlalchemy import text

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import declarative_base


Base = declarative_base()


class MemoryItem(Base):

    __tablename__ = "memory_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    memory_type = Column(
        Text,
        nullable=False
    )

    title = Column(
        Text,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    source = Column(Text)

    importance = Column(
        Text,
        nullable=False,
        default="medium"
    )

    confidence = Column(
        Numeric,
        nullable=False,
        default=1.0
    )

    status = Column(
        Text,
        nullable=False,
        default="active"
    )

    source_type = Column(Text)

    source_reference = Column(Text)

    access_count = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()")
    )
