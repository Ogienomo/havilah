"""Havilah OS — Initial Schema Migration

Auto-generated from SQLAlchemy model introspection.
Handles circular FK between approval_requests and risk_assessments.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('organizations',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('organization_type', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'active'")),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry', sa.Text(), nullable=True),
        sa.Column('website', sa.Text(), nullable=True),
    )

    op.create_table('contacts',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('organization_id', sa.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('full_name', sa.Text(), nullable=False),
        sa.Column('first_name', sa.Text(), nullable=True),
        sa.Column('last_name', sa.Text(), nullable=True),
        sa.Column('role_title', sa.Text(), nullable=True),
        sa.Column('email', sa.Text(), nullable=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('whatsapp_id', sa.Text(), nullable=True),
        sa.Column('linkedin_url', sa.Text(), nullable=True),
        sa.Column('relationship_status', sa.Text(), nullable=False, server_default=text("'active'")),
        sa.Column('priority_level', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('timezone', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    op.create_table('users',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('email', sa.Text(), nullable=False, unique=True),
        sa.Column('full_name', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'active'")),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('whatsapp_id', sa.Text(), nullable=True, unique=True),
    )

    op.create_table('projects',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('client_contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=True),
        sa.Column('organization_id', sa.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('objective', sa.Text(), nullable=True),
        sa.Column('project_type', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'active'")),
        sa.Column('priority', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('owner_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('meetings',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('meeting_type', sa.Text(), nullable=False, server_default=text("'internal'")),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'scheduled'")),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('organizer_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('participants', postgresql.JSONB(), nullable=True),
    )

    op.create_table('agenda_items',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('meeting_id', sa.UUID(as_uuid=True), sa.ForeignKey('meetings.id'), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default=text("'0'")),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('owner_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table('workflows',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('workflow_type', sa.Text(), nullable=False, server_default=text("'sequential'")),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'draft'")),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('owner_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('current_step_order', sa.Integer(), nullable=False, server_default=text("'0'")),
        sa.Column('auto_advance', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('trigger_rules', postgresql.JSONB(), nullable=True),
    )

    op.create_table('workflow_steps',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('workflow_id', sa.UUID(as_uuid=True), sa.ForeignKey('workflows.id'), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('step_order', sa.Integer(), nullable=False, server_default=text("'0'")),
        sa.Column('step_type', sa.Text(), nullable=False, server_default=text("'task'")),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('task_template', postgresql.JSONB(), nullable=True),
        sa.Column('approval_template', postgresql.JSONB(), nullable=True),
        sa.Column('agent_action', postgresql.JSONB(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('tasks',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('parent_task_id', sa.UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=True),
        sa.Column('workflow_step_id', sa.UUID(as_uuid=True), sa.ForeignKey('workflow_steps.id'), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('priority', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('owner_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assigned_to', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('block_reason', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('agents',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.Column('display_name', sa.Text(), nullable=False),
        sa.Column('agent_type', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'active'")),
        sa.Column('capabilities', postgresql.JSONB(), nullable=False),
        sa.Column('model_config', postgresql.JSONB(), nullable=True),
        sa.Column('tool_access', postgresql.JSONB(), nullable=False),
        sa.Column('approval_scope', sa.Text(), nullable=False, server_default=text("'none'")),
        sa.Column('max_concurrent_runs', sa.Integer(), nullable=False, server_default=text("'1'")),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=text('false')),
    )

    op.create_table('approval_requests',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('action_type', sa.Text(), nullable=False),
        sa.Column('channel', sa.Text(), nullable=False, server_default=text("'internal'")),
        sa.Column('intent_summary', sa.Text(), nullable=False),
        sa.Column('intent_detail', sa.Text(), nullable=True),
        sa.Column('draft_payload', postgresql.JSONB(), nullable=False),
        sa.Column('related_project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('related_contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=True),
        sa.Column('related_task_id', sa.UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=True),
        sa.Column('organization_id', sa.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('risk_level', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('approval_required', sa.Boolean(), nullable=False, server_default=text('true')),
        sa.Column('current_state', sa.Text(), nullable=False, server_default=text("'draft'")),
        sa.Column('approver_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('decision_note', sa.Text(), nullable=True),
        sa.Column('execution_status', sa.Text(), nullable=False, server_default=text("'not_started'")),
        sa.Column('rollback_possible', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('risk_assessment_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table('agent_runs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('agent_id', sa.UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('task_id', sa.UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=True),
        sa.Column('approval_id', sa.UUID(as_uuid=True), sa.ForeignKey('approval_requests.id'), nullable=True),
        sa.Column('workflow_step_id', sa.UUID(as_uuid=True), sa.ForeignKey('workflow_steps.id'), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'assigned'")),
        sa.Column('input_context', postgresql.JSONB(), nullable=False),
        sa.Column('configuration', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('token_usage', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )

    op.create_table('agent_results',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('agent_run_id', sa.UUID(as_uuid=True), sa.ForeignKey('agent_runs.id'), nullable=False),
        sa.Column('result_type', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('quality_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('is_actionable', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default=text('false')),
    )

    op.create_table('approval_decisions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('approval_request_id', sa.UUID(as_uuid=True), sa.ForeignKey('approval_requests.id'), nullable=False),
        sa.Column('decision_type', sa.Text(), nullable=False),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('decided_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('escalated_to', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table('approval_events',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('approval_request_id', sa.UUID(as_uuid=True), sa.ForeignKey('approval_requests.id'), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('actor_type', sa.Text(), nullable=False),
        sa.Column('actor_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('old_state', sa.Text(), nullable=True),
        sa.Column('new_state', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
    )

    op.create_table('approval_policies',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('risk_threshold', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('approval_mode', sa.Text(), nullable=False, server_default=text("'manual'")),
        sa.Column('auto_approve_below_threshold', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('required_approver_role', sa.Text(), nullable=True),
        sa.Column('expiration_hours', sa.Integer(), nullable=True),
        sa.Column('escalation_policy', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=text('true')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=text("'0'")),
    )

    op.create_table('communication_history',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=False),
        sa.Column('direction', sa.Text(), nullable=False),
        sa.Column('channel', sa.Text(), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'sent'")),
        sa.Column('approval_id', sa.UUID(as_uuid=True), sa.ForeignKey('approval_requests.id'), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('contact_preferences',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=False),
        sa.Column('preference_category', sa.Text(), nullable=False),
        sa.Column('preference_key', sa.Text(), nullable=False),
        sa.Column('preference_value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False, server_default=text("'1.0'")),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('content_drafts',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content_type', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'draft'")),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=True),
        sa.Column('approval_id', sa.UUID(as_uuid=True), sa.ForeignKey('approval_requests.id'), nullable=True),
        sa.Column('target_channel', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('owner_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table('content_comments',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('draft_id', sa.UUID(as_uuid=True), sa.ForeignKey('content_drafts.id'), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('comment_type', sa.Text(), nullable=False, server_default=text("'feedback'")),
        sa.Column('commented_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table('content_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('draft_id', sa.UUID(as_uuid=True), sa.ForeignKey('content_drafts.id'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default=text("'1'")),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=text('true')),
    )

    op.create_table('milestones',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('deliverables',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('milestone_id', sa.UUID(as_uuid=True), sa.ForeignKey('milestones.id'), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('deliverable_type', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('version_label', sa.Text(), nullable=True),
        sa.Column('file_id', sa.UUID(as_uuid=True), nullable=True),
    )

    op.create_table('departments',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('organization_id', sa.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('department_type', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'active'")),
        sa.Column('head_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table('domain_events',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('aggregate_type', sa.Text(), nullable=False),
        sa.Column('aggregate_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('event_category', sa.Text(), nullable=False, server_default=text("'domain'")),
        sa.Column('actor_type', sa.Text(), nullable=False, server_default=text("'system'")),
        sa.Column('actor_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('correlation_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('causation_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default=text("'1'")),
    )

    op.create_table('execution_records',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('approval_request_id', sa.UUID(as_uuid=True), sa.ForeignKey('approval_requests.id'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default=text("'1'")),
        sa.Column('execution_channel', sa.Text(), nullable=False),
        sa.Column('execution_status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('external_reference', sa.Text(), nullable=True),
        sa.Column('error_code', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result_payload', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('interactions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=False),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('channel', sa.Text(), nullable=False),
        sa.Column('interaction_type', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table('knowledge_artifacts',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('knowledge_type', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'draft'")),
        sa.Column('owner_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('canonical_version_id', sa.UUID(as_uuid=True), nullable=True),
    )

    op.create_table('knowledge_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('knowledge_artifact_id', sa.UUID(as_uuid=True), sa.ForeignKey('knowledge_artifacts.id'), nullable=False),
        sa.Column('version_label', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('change_note', sa.Text(), nullable=True),
        sa.Column('version_status', sa.Text(), nullable=False, server_default=text("'draft'")),
        sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('meeting_action_items',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('meeting_id', sa.UUID(as_uuid=True), sa.ForeignKey('meetings.id'), nullable=False),
        sa.Column('task_id', sa.UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('assigned_to', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
    )

    op.create_table('meeting_decisions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('meeting_id', sa.UUID(as_uuid=True), sa.ForeignKey('meetings.id'), nullable=False),
        sa.Column('decision_text', sa.Text(), nullable=False),
        sa.Column('decided_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
    )

    op.create_table('memory_items',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('memory_type', sa.Text(), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False, server_default=text("'global'")),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('related_contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=True),
        sa.Column('related_project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('related_task_id', sa.UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=True),
        sa.Column('source_type', sa.Text(), nullable=False, server_default=text("'user'")),
        sa.Column('source_reference', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False, server_default=text("'1.0'")),
        sa.Column('importance', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'active'")),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default=text("'0'")),
        sa.Column('reinforcement_count', sa.Integer(), nullable=False, server_default=text("'0'")),
        sa.Column('last_reinforced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('superseded_by', sa.UUID(as_uuid=True), sa.ForeignKey('memory_items.id'), nullable=True),
    )

    op.create_table('memory_events',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('memory_item_id', sa.UUID(as_uuid=True), sa.ForeignKey('memory_items.id'), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('old_status', sa.Text(), nullable=True),
        sa.Column('new_status', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
    )

    op.create_table('memory_links',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('memory_id', sa.UUID(as_uuid=True), sa.ForeignKey('memory_items.id'), nullable=False),
        sa.Column('linked_entity_type', sa.Text(), nullable=False),
        sa.Column('linked_entity_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.Text(), nullable=False, server_default=text("'related'")),
    )

    op.create_table('memory_sources',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('memory_item_id', sa.UUID(as_uuid=True), sa.ForeignKey('memory_items.id'), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_reference', sa.Text(), nullable=True),
        sa.Column('source_summary', sa.Text(), nullable=True),
        sa.Column('source_confidence', sa.Numeric(3, 2), nullable=True),
    )

    op.create_table('notifications',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('notification_type', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('category', sa.Text(), nullable=False, server_default=text("'operational'")),
        sa.Column('recipient_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('related_entity_type', sa.Text(), nullable=True),
        sa.Column('related_entity_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('action_url', sa.Text(), nullable=True),
        sa.Column('action_required', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('notification_deliveries',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('notification_id', sa.UUID(as_uuid=True), sa.ForeignKey('notifications.id'), nullable=False),
        sa.Column('channel', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('external_id', sa.Text(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )

    op.create_table('permissions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.Column('resource', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
    )

    op.create_table('project_links',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('linked_entity_type', sa.Text(), nullable=False),
        sa.Column('linked_entity_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('link_role', sa.Text(), nullable=False),
    )

    op.create_table('relationship_scores',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=False),
        sa.Column('score', sa.Numeric(5, 2), nullable=False, server_default=text("'50.0'")),
        sa.Column('score_type', sa.Text(), nullable=False, server_default=text("'overall'")),
        sa.Column('trend', sa.Text(), nullable=False, server_default=text("'stable'")),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    op.create_table('research_jobs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('project_id', sa.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('research_question', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'pending'")),
        sa.Column('priority', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('owner_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assigned_agent_run_id', sa.UUID(as_uuid=True), sa.ForeignKey('agent_runs.id'), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
    )

    op.create_table('research_sources',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('research_job_id', sa.UUID(as_uuid=True), sa.ForeignKey('research_jobs.id'), nullable=False),
        sa.Column('source_title', sa.Text(), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_reference', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_summary', sa.Text(), nullable=True),
        sa.Column('reliability_score', sa.Numeric(3, 2), nullable=True),
    )

    op.create_table('research_notes',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('research_job_id', sa.UUID(as_uuid=True), sa.ForeignKey('research_jobs.id'), nullable=False),
        sa.Column('source_id', sa.UUID(as_uuid=True), sa.ForeignKey('research_sources.id'), nullable=True),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('note_type', sa.Text(), nullable=False, server_default=text("'observation'")),
    )

    op.create_table('research_outputs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('research_job_id', sa.UUID(as_uuid=True), sa.ForeignKey('research_jobs.id'), nullable=False),
        sa.Column('output_type', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default=text("'draft'")),
    )

    op.create_table('risk_assessments',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('approval_request_id', sa.UUID(as_uuid=True), sa.ForeignKey('approval_requests.id'), nullable=True),
        sa.Column('risk_level', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('risk_score', sa.Numeric(5, 2), nullable=False, server_default=text("'50.0'")),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False, server_default=text("'0.5'")),
        sa.Column('approval_required', sa.Boolean(), nullable=False, server_default=text('true')),
        sa.Column('escalation_required', sa.Boolean(), nullable=False, server_default=text('false')),
        sa.Column('risk_factors', postgresql.JSONB(), nullable=False),
        sa.Column('mitigation_suggestions', postgresql.JSONB(), nullable=False),
        sa.Column('assessed_by', sa.Text(), nullable=False, server_default=text("'system'")),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table('roles',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=text('false')),
    )

    op.create_table('role_permissions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('role_id', sa.UUID(as_uuid=True), sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('permission_id', sa.UUID(as_uuid=True), sa.ForeignKey('permissions.id'), nullable=False),
    )

    op.create_table('stakeholders',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('organization_id', sa.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('contact_id', sa.UUID(as_uuid=True), sa.ForeignKey('contacts.id'), nullable=True),
        sa.Column('stakeholder_type', sa.Text(), nullable=False),
        sa.Column('influence_level', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('interest_level', sa.Text(), nullable=False, server_default=text("'medium'")),
        sa.Column('engagement_status', sa.Text(), nullable=False, server_default=text("'active'")),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    op.create_table('task_dependencies',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('blocking_task_id', sa.UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('blocked_task_id', sa.UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('dependency_type', sa.Text(), nullable=False, server_default=text("'finish_to_start'")),
    )

    op.create_table('user_roles',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role_id', sa.UUID(as_uuid=True), sa.ForeignKey('roles.id'), nullable=False),
    )

    op.create_table('workflow_transitions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=text('NOW()')),
        sa.Column('workflow_id', sa.UUID(as_uuid=True), sa.ForeignKey('workflows.id'), nullable=False),
        sa.Column('from_step_id', sa.UUID(as_uuid=True), sa.ForeignKey('workflow_steps.id'), nullable=True),
        sa.Column('to_step_id', sa.UUID(as_uuid=True), sa.ForeignKey('workflow_steps.id'), nullable=True),
        sa.Column('condition', postgresql.JSONB(), nullable=True),
        sa.Column('transition_type', sa.Text(), nullable=False, server_default=text("'on_complete'")),
    )

    # ── Add circular FK: approval_requests.risk_assessment_id → risk_assessments.id ──
    op.create_foreign_key(
        'fk_approval_requests_risk_assessment_id',
        'approval_requests',
        'risk_assessments',
        ['risk_assessment_id'],
        ['id'],
    )



def downgrade() -> None:
    # ── Remove circular FK first ──
    op.drop_constraint('fk_approval_requests_risk_assessment_id', 'approval_requests', type_='foreignkey')

    # ── Drop tables in reverse dependency order ──
    op.drop_table('workflow_transitions')
    op.drop_table('user_roles')
    op.drop_table('task_dependencies')
    op.drop_table('stakeholders')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('risk_assessments')
    op.drop_table('research_outputs')
    op.drop_table('research_notes')
    op.drop_table('research_sources')
    op.drop_table('research_jobs')
    op.drop_table('relationship_scores')
    op.drop_table('project_links')
    op.drop_table('permissions')
    op.drop_table('notification_deliveries')
    op.drop_table('notifications')
    op.drop_table('memory_sources')
    op.drop_table('memory_links')
    op.drop_table('memory_events')
    op.drop_table('memory_items')
    op.drop_table('meeting_decisions')
    op.drop_table('meeting_action_items')
    op.drop_table('knowledge_versions')
    op.drop_table('knowledge_artifacts')
    op.drop_table('interactions')
    op.drop_table('execution_records')
    op.drop_table('domain_events')
    op.drop_table('departments')
    op.drop_table('deliverables')
    op.drop_table('milestones')
    op.drop_table('content_versions')
    op.drop_table('content_comments')
    op.drop_table('content_drafts')
    op.drop_table('contact_preferences')
    op.drop_table('communication_history')
    op.drop_table('approval_policies')
    op.drop_table('approval_events')
    op.drop_table('approval_decisions')
    op.drop_table('agent_results')
    op.drop_table('agent_runs')
    op.drop_table('approval_requests')
    op.drop_table('agents')
    op.drop_table('tasks')
    op.drop_table('workflow_steps')
    op.drop_table('workflows')
    op.drop_table('agenda_items')
    op.drop_table('meetings')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('contacts')
    op.drop_table('organizations')
