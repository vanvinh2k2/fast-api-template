import sqlalchemy as sa

from alembic import op

revision = "1f4a6d8f3b2c"
down_revision = "f93c9c2ddf5c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_token_families",
        sa.Column("id", sa.Uuid(), primary_key=True, index=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True, index=True),
        sa.Column(
            "family_id",
            sa.Uuid(),
            sa.ForeignKey("refresh_token_families.id"),
            nullable=False,
        ),
        sa.Column("jti", sa.String(length=36), nullable=False, unique=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_jti", sa.String(length=36), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("refresh_token_families")
