"""fix campaign-donation relationship

Revision ID: 5f700aa8887a
Revises: 14a65a014733
Create Date: 2025-10-08 00:00:08.476469

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f700aa8887a'
down_revision = '14a65a014733'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('donation', schema=None) as batch_op:
        # 🔧 Prova a droppare la constraint (ignora errori se non esiste)
        try:
            batch_op.drop_constraint('fk_donation_campaign_id', type_='foreignkey')
        except Exception:
            pass

        # ✅ Ricrea la FK con nome e ondelete
        batch_op.create_foreign_key(
            'fk_donation_campaign_id',
            'campaign',
            ['campaign_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade():
    with op.batch_alter_table('donation', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('fk_donation_campaign_id', type_='foreignkey')
        except Exception:
            pass
        batch_op.create_foreign_key(
            'fk_donation_campaign_id',
            'campaign',
            ['campaign_id'],
            ['id']
        )
