from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy import Numeric
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import text

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import declarative_base


Base = declarative_base()


class ApprovalRequest(Base):

    __tablename__ = "approval_requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    action_type = Column(
        Text,
        nullable=False
    )

    summary = Column(
        Text,
        nullable=False
    )

    status = Column(
        Text,
        nullable=False,
        server_default=text("'pending'")
    )

    requested_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()")
    )

    approved_at = Column(
        DateTime(timezone=True)
    )

    category = Column(Text)

    current_state = Column(
        Text,
        nullable=False,
        server_default=text("'draft'")
    )

    risk_assessment_id = Column(
        UUID(as_uuid=True)
    )

    project_id = Column(
        UUID(as_uuid=True)
    )

    task_id = Column(
        UUID(as_uuid=True)
    )

    contact_id = Column(
        UUID(as_uuid=True)
    )

    organization_id = Column(
        UUID(as_uuid=True)
    )

    requested_by = Column(
        UUID(as_uuid=True)
    )

    confidence = Column(
        Numeric(5, 2)
    )

    decision_note = Column(
        Text
    )

    expires_at = Column(
        DateTime(timezone=True)
    )

    execution_status = Column(
        Text,
        server_default=text("'not_started'")
    )


class ApprovalDecision(Base):

    __tablename__ = "approval_decisions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    approval_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id"),
        nullable=False
    )

    decision_type = Column(
        Text,
        nullable=False
    )

    decision_reason = Column(
        Text
    )

    decided_by = Column(
        UUID(as_uuid=True)
    )

    decided_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()")
    )


class ExecutionRecord(Base):

    __tablename__ = "execution_records"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    approval_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id"),
        nullable=False
    )

    execution_status = Column(
        Text,
        nullable=False
    )

    execution_result = Column(
        JSONB
    )

    started_at = Column(
        DateTime(timezone=True)
    )

    completed_at = Column(
        DateTime(timezone=True)
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()")
    )
