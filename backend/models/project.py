from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy import text

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Project(Base):

    __tablename__ = "projects"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    name = Column(
        Text,
        nullable=False
    )

    description = Column(
        Text
    )

    status = Column(
        Text,
        nullable=False,
        server_default=text("'active'")
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
