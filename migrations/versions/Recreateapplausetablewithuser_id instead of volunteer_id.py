"""Recreate applause table with user_id instead of volunteer_id"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a24713ad400d'
down_revision = 'f73736addd9c'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old table
    op.drop_table("applause")

    # Recreate table with user_id instead of volunteer_id
    op.create_table(
        "applause",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("post_id", sa.Integer, sa.ForeignKey("post.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_user_applause"),
    )
    op.create_index("ix_applause_post_id", "applause", ["post_id"])
    op.create_index("ix_applause_user_id", "applause", ["user_id"])


def downgrade():
    # Drop new table
    op.drop_table("applause")

    # Recreate old table with volunteer_id
    op.create_table(
        "applause",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("post_id", sa.Integer, sa.ForeignKey("post.id", ondelete="CASCADE"), nullable=False),
        sa.Column("volunteer_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("post_id", "volunteer_id", name="uq_post_applause_unique"),
    )
    op.create_index("ix_applause_post_id", "applause", ["post_id"])
    op.create_index("ix_applause_volunteer_id", "applause", ["volunteer_id"])
