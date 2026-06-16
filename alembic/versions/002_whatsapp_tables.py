"""Havilah OS — WhatsApp Domain Tables

Adds the 4 tables required by the WhatsApp bridge:
  - whatsapp_sessions
  - whatsapp_messages
  - whatsapp_templates
  - whatsapp_approval_votes

These were defined in backend/models/whatsapp.py but never included
in migration 001_initial_schema. They are needed for:
  - /api/whatsapp/webhook (POST) — persists every inbound/outbound message
  - WhatsAppBridge.process_incoming_message() — looks up or creates a session
  - Approval flow via WhatsApp — tracks votes cast via interactive buttons

Revision ID: 002
Revises: 001
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── whatsapp_sessions ────────────────────────────────────────────────
    # Must exist BEFORE whatsapp_messages and whatsapp_approval_votes
    # (both FK to whatsapp_sessions.id).
    op.create_table('whatsapp_sessions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False,
                  server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('phone_number', sa.Text(), nullable=False),
        sa.Column('whatsapp_id', sa.Text(), nullable=True),
        sa.Column('user_id', sa.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('contact_id', sa.UUID(as_uuid=True),
                  sa.ForeignKey('contacts.id'), nullable=True),
        sa.Column('status', sa.Text(), nullable=False,
                  server_default=text("'active'")),
        sa.Column('session_context', postgresql.JSONB(), nullable=True,
                  server_default=text("'{}'::jsonb")),
        sa.Column('language', sa.Text(), nullable=False,
                  server_default=text("'en'")),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_inbound_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_outbound_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False,
                  server_default=text('0')),
        sa.Column('opted_in', sa.Boolean(), nullable=False,
                  server_default=text('false')),
        sa.Column('opted_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opted_out_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_whatsapp_sessions_phone_number', 'whatsapp_sessions',
                    ['phone_number'], unique=True)
    op.create_index('ix_whatsapp_sessions_whatsapp_id', 'whatsapp_sessions',
                    ['whatsapp_id'], unique=True)

    # ── whatsapp_messages ────────────────────────────────────────────────
    op.create_table('whatsapp_messages',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False,
                  server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('session_id', sa.UUID(as_uuid=True),
                  sa.ForeignKey('whatsapp_sessions.id'), nullable=False),
        sa.Column('direction', sa.Text(), nullable=False),
        sa.Column('message_type', sa.Text(), nullable=False,
                  server_default=text("'text'")),
        sa.Column('status', sa.Text(), nullable=False,
                  server_default=text("'pending'")),
        sa.Column('content_body', sa.Text(), nullable=True),
        sa.Column('media_url', sa.Text(), nullable=True),
        sa.Column('media_type', sa.Text(), nullable=True),
        sa.Column('interactive_type', sa.Text(), nullable=True),
        sa.Column('interactive_payload', postgresql.JSONB(), nullable=True),
        sa.Column('template_name', sa.Text(), nullable=True),
        sa.Column('template_parameters', postgresql.JSONB(), nullable=True),
        sa.Column('whatsapp_message_id', sa.Text(), nullable=True),
        sa.Column('external_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sender_phone', sa.Text(), nullable=True),
        sa.Column('recipient_phone', sa.Text(), nullable=True),
        sa.Column('related_entity_type', sa.Text(), nullable=True),
        sa.Column('related_entity_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('approval_id', sa.UUID(as_uuid=True),
                  sa.ForeignKey('approval_requests.id'), nullable=True),
        sa.Column('error_code', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_whatsapp_messages_session_id', 'whatsapp_messages',
                    ['session_id'])
    op.create_index('ix_whatsapp_messages_whatsapp_message_id', 'whatsapp_messages',
                    ['whatsapp_message_id'], unique=True)

    # ── whatsapp_templates ───────────────────────────────────────────────
    op.create_table('whatsapp_templates',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False,
                  server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('language', sa.Text(), nullable=False,
                  server_default=text("'en'")),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('header_type', sa.Text(), nullable=True),
        sa.Column('header_text', sa.Text(), nullable=True),
        sa.Column('footer_text', sa.Text(), nullable=True),
        sa.Column('button_type', sa.Text(), nullable=True),
        sa.Column('button_payload', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False,
                  server_default=text("'draft'")),
        sa.Column('external_template_id', sa.Text(), nullable=True),
        sa.Column('quality_score', sa.Text(), nullable=True),
        sa.Column('use_count', sa.Integer(), nullable=False,
                  server_default=text('0')),
    )
    op.create_index('ix_whatsapp_templates_name', 'whatsapp_templates',
                    ['name'], unique=True)

    # ── whatsapp_approval_votes ──────────────────────────────────────────
    op.create_table('whatsapp_approval_votes',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, nullable=False,
                  server_default=text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=text('NOW()')),
        sa.Column('session_id', sa.UUID(as_uuid=True),
                  sa.ForeignKey('whatsapp_sessions.id'), nullable=False),
        sa.Column('approval_id', sa.UUID(as_uuid=True),
                  sa.ForeignKey('approval_requests.id'), nullable=False),
        sa.Column('message_id', sa.UUID(as_uuid=True),
                  sa.ForeignKey('whatsapp_messages.id'), nullable=True),
        sa.Column('vote', sa.Text(), nullable=False),
        sa.Column('vote_source', sa.Text(), nullable=False,
                  server_default=text("'whatsapp_button'")),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False,
                  server_default=text('false')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index('ix_whatsapp_approval_votes_session_id',
                    'whatsapp_approval_votes', ['session_id'])
    op.create_index('ix_whatsapp_approval_votes_approval_id',
                    'whatsapp_approval_votes', ['approval_id'])


def downgrade() -> None:
    op.drop_index('ix_whatsapp_approval_votes_approval_id', table_name='whatsapp_approval_votes')
    op.drop_index('ix_whatsapp_approval_votes_session_id', table_name='whatsapp_approval_votes')
    op.drop_table('whatsapp_approval_votes')

    op.drop_index('ix_whatsapp_templates_name', table_name='whatsapp_templates')
    op.drop_table('whatsapp_templates')

    op.drop_index('ix_whatsapp_messages_whatsapp_message_id', table_name='whatsapp_messages')
    op.drop_index('ix_whatsapp_messages_session_id', table_name='whatsapp_messages')
    op.drop_table('whatsapp_messages')

    op.drop_index('ix_whatsapp_sessions_whatsapp_id', table_name='whatsapp_sessions')
    op.drop_index('ix_whatsapp_sessions_phone_number', table_name='whatsapp_sessions')
    op.drop_table('whatsapp_sessions')
