"""Initial schema - create all tables.

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vendors table
    op.create_table(
        'vendors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('contact_name', sa.String(255)),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('work_order_number', sa.String(50), unique=True, nullable=False),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vendors.id'), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('region', sa.String(100)),
        sa.Column('status', sa.String(50), nullable=False, default='authorized'),
        sa.Column('priority', sa.String(20), nullable=False, default='normal'),
        sa.Column('authorized_date', sa.Date()),
        sa.Column('sent_to_vendor_date', sa.Date()),
        sa.Column('received_from_vendor_date', sa.Date()),
        sa.Column('target_completion_date', sa.Date()),
        sa.Column('actual_completion_date', sa.Date()),
        sa.Column('revision_count', sa.Integer(), default=0, nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_projects_work_order_number', 'projects', ['work_order_number'])
    op.create_index('ix_projects_vendor_id', 'projects', ['vendor_id'])
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_region', 'projects', ['region'])

    # Create milestones table
    op.create_table(
        'milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stage', sa.String(50), nullable=False),
        sa.Column('expected_date', sa.Date()),
        sa.Column('actual_date', sa.Date()),
        sa.Column('sla_days', sa.Integer()),
        sa.Column('is_overdue', sa.Boolean(), default=False, nullable=False),
        sa.Column('days_overdue', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_milestones_project_id', 'milestones', ['project_id'])

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, default='info'),
        sa.Column('is_acknowledged', sa.Boolean(), default=False, nullable=False),
        sa.Column('acknowledged_at', sa.DateTime()),
        sa.Column('acknowledged_by', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_alerts_project_id', 'alerts', ['project_id'])
    op.create_index('ix_alerts_alert_type', 'alerts', ['alert_type'])
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_is_acknowledged', 'alerts', ['is_acknowledged'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('field_name', sa.String(100)),
        sa.Column('old_value', sa.Text()),
        sa.Column('new_value', sa.Text()),
        sa.Column('changes', postgresql.JSONB()),
        sa.Column('user_id', sa.String(255)),
        sa.Column('user_email', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_logs_project_id', 'audit_logs', ['project_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # Create vendor_metrics table
    op.create_table(
        'vendor_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vendor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vendors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_projects', sa.Integer(), default=0, nullable=False),
        sa.Column('completed_projects', sa.Integer(), default=0, nullable=False),
        sa.Column('active_projects', sa.Integer(), default=0, nullable=False),
        sa.Column('overdue_projects', sa.Integer(), default=0, nullable=False),
        sa.Column('on_time_rate', sa.Float(), default=0.0, nullable=False),
        sa.Column('avg_cycle_time_days', sa.Float()),
        sa.Column('revision_rate', sa.Float(), default=0.0, nullable=False),
        sa.Column('sla_compliance_rate', sa.Float(), default=0.0, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_vendor_metrics_vendor_id', 'vendor_metrics', ['vendor_id'])
    op.create_index('ix_vendor_metrics_period_start', 'vendor_metrics', ['period_start'])


def downgrade() -> None:
    op.drop_table('vendor_metrics')
    op.drop_table('audit_logs')
    op.drop_table('alerts')
    op.drop_table('milestones')
    op.drop_table('projects')
    op.drop_table('vendors')
