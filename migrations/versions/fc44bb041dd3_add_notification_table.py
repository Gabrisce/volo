"""add notification table

Revision ID: fc44bb041dd3
Revises: 4934bb0f1bd2
Create Date: 2025-08-28 17:53:51.748476

"""
from alembic import op
import sqlalchemy as sa
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'fc44bb041dd3'
down_revision = '4934bb0f1bd2'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'notification',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False, index=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('url', sa.String(255)),
        sa.Column('is_read', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
    )

def downgrade():
    op.drop_table('notification')