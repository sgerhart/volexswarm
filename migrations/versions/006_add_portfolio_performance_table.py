"""Add portfolio performance table for tracking starting balances and returns

Revision ID: 006
Revises: 005
Create Date: 2025-08-16 19:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Create portfolio_performance table."""
    
    # Create portfolio_performance table
    op.create_table('portfolio_performance',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('initial_balance', sa.Float, nullable=False),  # Starting portfolio value
        sa.Column('initial_timestamp', sa.DateTime, nullable=False),  # When balance was first recorded
        sa.Column('current_balance', sa.Float, nullable=False),  # Current portfolio value
        sa.Column('last_updated', sa.DateTime, nullable=False),  # Last update timestamp
        sa.Column('absolute_return', sa.Float, default=0.0),  # Absolute dollar return
        sa.Column('total_return_percentage', sa.Float, default=0.0),  # Percentage return
        sa.Column('realized_pnl', sa.Float, default=0.0),  # Realized profit/loss
        sa.Column('unrealized_pnl', sa.Float, default=0.0),  # Unrealized profit/loss
        sa.Column('daily_return', sa.Float, default=0.0),  # Daily return amount
        sa.Column('annualized_return', sa.Float, default=0.0),  # Annualized return percentage
        sa.Column('days_elapsed', sa.Integer, default=0),  # Days since initial balance
        sa.Column('performance_metadata', postgresql.JSONB),  # Additional performance data
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_portfolio_performance_exchange', 'portfolio_performance', ['exchange'])
    op.create_index('idx_portfolio_performance_timestamp', 'portfolio_performance', ['initial_timestamp'])
    op.create_index('idx_portfolio_performance_last_updated', 'portfolio_performance', ['last_updated'])
    
    # Create unique constraint on exchange (one record per exchange)
    op.create_unique_constraint('uq_portfolio_performance_exchange', 'portfolio_performance', ['exchange'])


def downgrade():
    """Drop portfolio_performance table."""
    
    # Drop indexes
    op.drop_index('idx_portfolio_performance_last_updated', table_name='portfolio_performance')
    op.drop_index('idx_portfolio_performance_timestamp', table_name='portfolio_performance')
    op.drop_index('idx_portfolio_performance_exchange', table_name='portfolio_performance')
    
    # Drop table
    op.drop_table('portfolio_performance')
