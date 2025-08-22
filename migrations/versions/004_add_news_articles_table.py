"""Add news articles table

Revision ID: 004
Revises: 003
Create Date: 2025-01-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create news_articles table
    op.create_table('news_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('sentiment_label', sa.String(length=20), nullable=True),
        sa.Column('impact_score', sa.Float(), nullable=True),
        sa.Column('relevant_keywords', sa.JSON(), nullable=True),
        sa.Column('trading_implications', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    
    # Create indexes for better performance
    op.create_index('idx_news_articles_published_at', 'news_articles', ['published_at'])
    op.create_index('idx_news_articles_source', 'news_articles', ['source'])
    op.create_index('idx_news_articles_sentiment_label', 'news_articles', ['sentiment_label'])
    op.create_index('idx_news_articles_sentiment_score', 'news_articles', ['sentiment_score'])
    op.create_index('idx_news_articles_impact_score', 'news_articles', ['impact_score'])
    
    # Create sentiment_analysis table for detailed sentiment tracking
    op.create_table('sentiment_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('news_article_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('sentiment_label', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('entities', sa.JSON(), nullable=True),
        sa.Column('impact_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['news_article_id'], ['news_articles.id'], ondelete='CASCADE')
    )
    
    # Create trading_signals table for news-based signals
    op.create_table('trading_signals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('signal_type', sa.String(length=10), nullable=False),  # buy, sell, hold
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('impact_score', sa.Float(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('news_articles', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),  # news_sentiment, technical, etc.
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for trading signals
    op.create_index('idx_trading_signals_symbol', 'trading_signals', ['symbol'])
    op.create_index('idx_trading_signals_signal_type', 'trading_signals', ['signal_type'])
    op.create_index('idx_trading_signals_created_at', 'trading_signals', ['created_at'])
    op.create_index('idx_trading_signals_source', 'trading_signals', ['source'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_trading_signals_source', table_name='trading_signals')
    op.drop_index('idx_trading_signals_created_at', table_name='trading_signals')
    op.drop_index('idx_trading_signals_signal_type', table_name='trading_signals')
    op.drop_index('idx_trading_signals_symbol', table_name='trading_signals')
    op.drop_index('idx_news_articles_impact_score', table_name='news_articles')
    op.drop_index('idx_news_articles_sentiment_score', table_name='news_articles')
    op.drop_index('idx_news_articles_sentiment_label', table_name='news_articles')
    op.drop_index('idx_news_articles_source', table_name='news_articles')
    op.drop_index('idx_news_articles_published_at', table_name='news_articles')
    
    # Drop tables
    op.drop_table('trading_signals')
    op.drop_table('sentiment_analysis')
    op.drop_table('news_articles') 