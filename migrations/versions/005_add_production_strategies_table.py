"""Add production strategies table

Revision ID: 005
Revises: 004
Create Date: 2025-01-28 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Create production_strategies table."""
    
    # Create production_strategies table
    op.create_table('production_strategies',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('parameters', postgresql.JSONB),
        sa.Column('risk_profile', sa.String(20), default='balanced'),
        sa.Column('status', sa.String(20), default='active'),  # active, paused, inactive, deactivated
        sa.Column('allocation', postgresql.JSONB),  # Capital allocation settings
        sa.Column('risk_limits', postgresql.JSONB),  # Risk management limits
        sa.Column('monitoring_config', postgresql.JSONB),  # Monitoring configuration
        sa.Column('strategy_metadata', postgresql.JSONB),  # Additional metadata
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_production_strategies_status', 'production_strategies', ['status'])
    op.create_index('idx_production_strategies_symbol', 'production_strategies', ['symbol'])
    op.create_index('idx_production_strategies_type', 'production_strategies', ['type'])
    op.create_index('idx_production_strategies_created', 'production_strategies', ['created_at'])
    op.create_index('idx_production_strategies_updated', 'production_strategies', ['updated_at'])


def downgrade():
    """Drop production_strategies table."""
    
    # Drop indexes
    op.drop_index('idx_production_strategies_updated', table_name='production_strategies')
    op.drop_index('idx_production_strategies_created', table_name='production_strategies')
    op.drop_index('idx_production_strategies_type', table_name='production_strategies')
    op.drop_index('idx_production_strategies_symbol', table_name='production_strategies')
    op.drop_index('idx_production_strategies_status', table_name='production_strategies')
    
    # Drop table
    op.drop_table('production_strategies') 