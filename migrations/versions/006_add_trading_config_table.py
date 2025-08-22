"""Add trading configuration table for simulation mode settings

Revision ID: 006
Revises: 005_add_production_strategies_table
Create Date: 2025-08-17 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005_add_production_strategies_table'
branch_labels = None
depends_on = None


def upgrade():
    """Create trading_config table for simulation mode settings."""
    
    # Create trading_config table
    op.create_table('trading_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(length=100), nullable=False),
        sa.Column('config_value', sa.Text(), nullable=False),  # JSON string
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key')
    )
    
    # Create index for faster lookups
    op.create_index('idx_trading_config_key', 'trading_config', ['config_key'])
    op.create_index('idx_trading_config_enabled', 'trading_config', ['enabled'])
    
    # Insert default trading configuration
    op.execute("""
        INSERT INTO trading_config (config_key, config_value, description, enabled) VALUES
        ('trading_mode', '"simulation"', 'Current trading mode: simulation, real_trading, hybrid, sandbox, backtest', true),
        ('simulation_balance', '10000.0', 'Starting balance for simulation accounts', true),
        ('max_simulation_risk', '0.02', 'Maximum risk per trade in simulation (2%)', true),
        ('real_trading_enabled', 'false', 'Whether real trading is allowed', true),
        ('simulation_accounts', '["simulation_main", "simulation_test"]', 'List of simulation account names', true),
        ('real_accounts', '["binance_us_main"]', 'List of real trading account names', true),
        ('safety_checks_enabled', 'true', 'Whether safety checks are active', true),
        ('max_position_size', '0.1', 'Maximum position size as percentage of portfolio (10%)', true),
        ('emergency_stop_enabled', 'true', 'Whether emergency stop is active', true)
    """)


def downgrade():
    """Remove trading_config table."""
    op.drop_index('idx_trading_config_enabled', 'trading_config')
    op.drop_index('idx_trading_config_key', 'trading_config')
    op.drop_table('trading_config')
