"""
VolexSwarm Agentic Compliance Agent - Autonomous Regulatory Compliance and Audit Management
Transforms the Compliance Agent into an AutoGen AssistantAgent for autonomous compliance monitoring.
Part of Phase 2.7: Compliance Agent → AutoGen AssistantAgent
"""

import sys
import os
import logging
import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import sqlite3
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Trade, Order
from common.websocket_client import AgentWebSocketClient, MessageType
from agents.agentic_framework.agent_templates import BaseAgent, AgentConfig

# Initialize structured logger
logger = get_logger("agentic_compliance")

# Compliance configuration
COMPLIANCE_CONFIG = {
    "audit_log_retention_days": 2555,  # 7 years for regulatory compliance
    "trade_reporting_enabled": True,
    "kyc_required": True,
    "aml_checks_enabled": True,
    "suspicious_activity_threshold": 10000,  # $10k threshold
    "daily_trade_limit": 100000,  # $100k daily limit
    "regulatory_jurisdiction": "US",  # Default jurisdiction
    "reporting_frequency": "daily",  # daily, weekly, monthly
    "audit_trail_encryption": True,
    "compliance_checks_enabled": True
}

# Local audit database
AUDIT_DB_PATH = os.path.join(os.getcwd(), "data", "audit_trail.db")


@dataclass
class TradeLogRequest:
    """Request model for trade logging."""
    trade_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: datetime
    exchange: str
    order_id: str
    user_id: Optional[str] = None
    strategy_id: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None


@dataclass
class ComplianceCheckRequest:
    """Request model for compliance checks."""
    user_id: str
    trade_amount: float
    symbol: str
    side: str
    exchange: str
    timestamp: datetime
    kyc_status: Optional[str] = None
    aml_status: Optional[str] = None


@dataclass
class AuditTrailRequest:
    """Request model for audit trail queries."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    symbol: Optional[str] = None
    action_type: Optional[str] = None
    limit: int = 100
    offset: int = 0


@dataclass
class RegulatoryReportRequest:
    """Request model for regulatory reporting."""
    report_type: str  # 'daily', 'weekly', 'monthly', 'custom'
    start_date: datetime
    end_date: datetime
    jurisdiction: str = "US"
    format: str = "json"  # 'json', 'csv', 'xml'


class ComplianceManager:
    """Manages compliance operations and audit trails."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.audit_db = None
        self.initialize_audit_database()
        
    def initialize_audit_database(self):
        """Initialize local audit database."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(AUDIT_DB_PATH), exist_ok=True)
            
            # Initialize SQLite database
            self.audit_db = sqlite3.connect(AUDIT_DB_PATH)
            cursor = self.audit_db.cursor()
            
            # Create audit trail table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    action_type TEXT NOT NULL,
                    user_id TEXT,
                    symbol TEXT,
                    trade_id TEXT,
                    order_id TEXT,
                    amount REAL,
                    details TEXT,
                    compliance_status TEXT,
                    regulatory_flags TEXT,
                    hash TEXT NOT NULL
                )
            ''')
            
            # Create compliance checks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user_id TEXT NOT NULL,
                    check_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    flags TEXT
                )
            ''')
            
            # Create regulatory reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS regulatory_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    report_type TEXT NOT NULL,
                    start_date DATETIME NOT NULL,
                    end_date DATETIME NOT NULL,
                    jurisdiction TEXT NOT NULL,
                    status TEXT NOT NULL,
                    file_path TEXT,
                    hash TEXT NOT NULL
                )
            ''')
            
            self.audit_db.commit()
            logger.info("Audit database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize audit database: {str(e)}")
            raise
    
    def generate_audit_hash(self, data: str) -> str:
        """Generate SHA-256 hash for audit trail integrity."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def log_trade(self, request: TradeLogRequest) -> Dict[str, Any]:
        """Log a trade for audit and compliance purposes."""
        try:
            audit_id = str(uuid.uuid4())
            timestamp = request.timestamp or datetime.now()
            
            # Calculate trade amount
            trade_amount = request.quantity * request.price
            
            # Create audit record
            audit_data = {
                "audit_id": audit_id,
                "timestamp": timestamp,
                "action_type": "trade_execution",
                "user_id": request.user_id or "system",
                "symbol": request.symbol,
                "trade_id": request.trade_id,
                "order_id": request.order_id,
                "amount": trade_amount,
                "details": json.dumps({
                    "side": request.side,
                    "quantity": request.quantity,
                    "price": request.price,
                    "exchange": request.exchange,
                    "strategy_id": request.strategy_id,
                    "risk_assessment": request.risk_assessment
                }),
                "compliance_status": "pending",
                "regulatory_flags": json.dumps([])
            }
            
            # Generate hash for integrity
            audit_data["hash"] = self.generate_audit_hash(
                f"{audit_id}{timestamp}{request.symbol}{trade_amount}"
            )
            
            # Store in audit database
            cursor = self.audit_db.cursor()
            cursor.execute('''
                INSERT INTO audit_trail 
                (audit_id, timestamp, action_type, user_id, symbol, trade_id, order_id, 
                 amount, details, compliance_status, regulatory_flags, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                audit_data["audit_id"], audit_data["timestamp"], audit_data["action_type"],
                audit_data["user_id"], audit_data["symbol"], audit_data["trade_id"],
                audit_data["order_id"], audit_data["amount"], audit_data["details"],
                audit_data["compliance_status"], audit_data["regulatory_flags"], audit_data["hash"]
            ))
            
            self.audit_db.commit()
            
            # Perform compliance checks
            compliance_result = self.perform_compliance_checks(
                request.user_id or "system", trade_amount, request.symbol, request.side
            )
            
            # Update compliance status
            if compliance_result["all_checks_passed"]:
                cursor.execute('''
                    UPDATE audit_trail 
                    SET compliance_status = ? 
                    WHERE audit_id = ?
                ''', ("approved", audit_id))
                self.audit_db.commit()
            
            return {
                "audit_id": audit_id,
                "trade_id": request.trade_id,
                "compliance_status": "approved" if compliance_result["all_checks_passed"] else "flagged",
                "compliance_checks": compliance_result,
                "timestamp": timestamp,
                "hash": audit_data["hash"]
            }
            
        except Exception as e:
            logger.error(f"Error logging trade: {str(e)}")
            raise Exception(f"Trade logging failed: {str(e)}")
    
    def perform_compliance_checks(self, user_id: str, trade_amount: float, 
                                symbol: str, side: str) -> Dict[str, Any]:
        """Perform comprehensive compliance checks."""
        try:
            check_id = str(uuid.uuid4())
            timestamp = datetime.now()
            flags = []
            
            # KYC Check (placeholder - would integrate with real KYC service)
            kyc_status = "verified"  # Placeholder
            if self.config["kyc_required"] and kyc_status != "verified":
                flags.append("kyc_required")
            
            # AML Check (placeholder - would integrate with real AML service)
            aml_status = "clear"  # Placeholder
            if self.config["aml_checks_enabled"] and aml_status != "clear":
                flags.append("aml_flagged")
            
            # Suspicious Activity Check
            if trade_amount > self.config["suspicious_activity_threshold"]:
                flags.append("large_transaction")
            
            # Daily Trade Limit Check
            daily_total = self.get_daily_trade_total(user_id)
            if daily_total + trade_amount > self.config["daily_trade_limit"]:
                flags.append("daily_limit_exceeded")
            
            # Pattern Analysis (simplified)
            if self.detect_suspicious_patterns(user_id, symbol, trade_amount):
                flags.append("suspicious_pattern")
            
            # Store compliance check
            cursor = self.audit_db.cursor()
            cursor.execute('''
                INSERT INTO compliance_checks 
                (check_id, timestamp, user_id, check_type, status, details, flags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                check_id, timestamp, user_id, "trade_compliance",
                "passed" if not flags else "flagged",
                json.dumps({
                    "trade_amount": trade_amount,
                    "symbol": symbol,
                    "side": side,
                    "kyc_status": kyc_status,
                    "aml_status": aml_status,
                    "daily_total": daily_total
                }),
                json.dumps(flags)
            ))
            
            self.audit_db.commit()
            
            return {
                "check_id": check_id,
                "all_checks_passed": len(flags) == 0,
                "flags": flags,
                "kyc_status": kyc_status,
                "aml_status": aml_status,
                "daily_total": daily_total,
                "thresholds": {
                    "suspicious_activity": self.config["suspicious_activity_threshold"],
                    "daily_limit": self.config["daily_trade_limit"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error performing compliance checks: {str(e)}")
            return {
                "check_id": str(uuid.uuid4()),
                "all_checks_passed": False,
                "flags": ["compliance_check_error"],
                "error": str(e)
            }
    
    def get_daily_trade_total(self, user_id: str) -> float:
        """Get total trade amount for user today."""
        try:
            cursor = self.audit_db.cursor()
            today = datetime.now().date()
            
            cursor.execute('''
                SELECT SUM(amount) FROM audit_trail 
                WHERE user_id = ? AND DATE(timestamp) = ? AND action_type = 'trade_execution'
            ''', (user_id, today))
            
            result = cursor.fetchone()
            return result[0] or 0.0
            
        except Exception as e:
            logger.error(f"Error getting daily trade total: {str(e)}")
            return 0.0
    
    def detect_suspicious_patterns(self, user_id: str, symbol: str, amount: float) -> bool:
        """Detect suspicious trading patterns (simplified implementation)."""
        try:
            cursor = self.audit_db.cursor()
            
            # Check for rapid successive trades
            cursor.execute('''
                SELECT COUNT(*) FROM audit_trail 
                WHERE user_id = ? AND symbol = ? AND action_type = 'trade_execution'
                AND timestamp > datetime('now', '-1 hour')
            ''', (user_id, symbol))
            
            recent_trades = cursor.fetchone()[0]
            
            # Flag if more than 10 trades in the last hour
            if recent_trades > 10:
                return True
            
            # Check for unusual amount patterns
            cursor.execute('''
                SELECT AVG(amount) FROM audit_trail 
                WHERE user_id = ? AND action_type = 'trade_execution'
                AND timestamp > datetime('now', '-7 days')
            ''', (user_id,))
            
            avg_amount = cursor.fetchone()[0] or 0
            
            # Flag if amount is significantly different from average
            if avg_amount > 0 and (amount > avg_amount * 5 or amount < avg_amount * 0.2):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting suspicious patterns: {str(e)}")
            return False
    
    def get_audit_trail(self, request: AuditTrailRequest) -> Dict[str, Any]:
        """Retrieve audit trail with filtering and pagination."""
        try:
            cursor = self.audit_db.cursor()
            
            # Build query
            query = "SELECT * FROM audit_trail WHERE 1=1"
            params = []
            
            if request.start_date:
                query += " AND timestamp >= ?"
                params.append(request.start_date)
            
            if request.end_date:
                query += " AND timestamp <= ?"
                params.append(request.end_date)
            
            if request.user_id:
                query += " AND user_id = ?"
                params.append(request.user_id)
            
            if request.symbol:
                query += " AND symbol = ?"
                params.append(request.symbol)
            
            if request.action_type:
                query += " AND action_type = ?"
                params.append(request.action_type)
            
            # Add ordering and pagination
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([request.limit, request.offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            audit_records = []
            for row in rows:
                record = dict(zip(columns, row))
                # Parse JSON fields
                if record.get('details'):
                    record['details'] = json.loads(record['details'])
                if record.get('regulatory_flags'):
                    record['regulatory_flags'] = json.loads(record['regulatory_flags'])
                audit_records.append(record)
            
            # Get total count
            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            count_query = count_query.split("ORDER BY")[0]  # Remove ordering and pagination
            cursor.execute(count_query, params[:-2])  # Remove limit and offset
            total_count = cursor.fetchone()[0]
            
            return {
                "audit_records": audit_records,
                "total_count": total_count,
                "limit": request.limit,
                "offset": request.offset,
                "has_more": len(audit_records) == request.limit
            }
            
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {str(e)}")
            raise Exception(f"Audit trail retrieval failed: {str(e)}")
    
    def generate_regulatory_report(self, request: RegulatoryReportRequest) -> Dict[str, Any]:
        """Generate regulatory compliance report."""
        try:
            report_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Get audit data for the period
            cursor = self.audit_db.cursor()
            cursor.execute('''
                SELECT * FROM audit_trail 
                WHERE timestamp BETWEEN ? AND ? AND action_type = 'trade_execution'
                ORDER BY timestamp
            ''', (request.start_date, request.end_date))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            # Process audit data
            trades = []
            total_volume = 0
            unique_users = set()
            unique_symbols = set()
            
            for row in rows:
                record = dict(zip(columns, row))
                if record.get('details'):
                    record['details'] = json.loads(record['details'])
                if record.get('regulatory_flags'):
                    record['regulatory_flags'] = json.loads(record['regulatory_flags'])
                
                trades.append(record)
                total_volume += record['amount']
                unique_users.add(record['user_id'])
                unique_symbols.add(record['symbol'])
            
            # Generate report data
            report_data = {
                "report_id": report_id,
                "report_type": request.report_type,
                "jurisdiction": request.jurisdiction,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "generated_at": timestamp.isoformat(),
                "summary": {
                    "total_trades": len(trades),
                    "total_volume": total_volume,
                    "unique_users": len(unique_users),
                    "unique_symbols": len(unique_symbols),
                    "average_trade_size": total_volume / len(trades) if trades else 0
                },
                "compliance_metrics": {
                    "flagged_trades": len([t for t in trades if t['compliance_status'] == 'flagged']),
                    "approved_trades": len([t for t in trades if t['compliance_status'] == 'approved']),
                    "suspicious_activity_count": len([t for t in trades if 'large_transaction' in t.get('regulatory_flags', [])])
                },
                "trades": trades
            }
            
            # Store report metadata
            cursor.execute('''
                INSERT INTO regulatory_reports 
                (report_id, timestamp, report_type, start_date, end_date, jurisdiction, status, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id, timestamp, request.report_type, request.start_date,
                request.end_date, request.jurisdiction, "generated",
                self.generate_audit_hash(json.dumps(report_data))
            ))
            
            self.audit_db.commit()
            
            return {
                "report_id": report_id,
                "status": "generated",
                "format": request.format,
                "data": report_data if request.format == "json" else None,
                "hash": self.generate_audit_hash(json.dumps(report_data)),
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error generating regulatory report: {str(e)}")
            raise Exception(f"Report generation failed: {str(e)}")
    
    def get_compliance_status(self, user_id: str) -> Dict[str, Any]:
        """Get compliance status for a user."""
        try:
            cursor = self.audit_db.cursor()
            
            # Get recent compliance checks
            cursor.execute('''
                SELECT * FROM compliance_checks 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''', (user_id,))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            compliance_checks = []
            for row in rows:
                record = dict(zip(columns, row))
                if record.get('details'):
                    try:
                        record['details'] = json.loads(record['details'])
                    except json.JSONDecodeError:
                        record['details'] = {}
                if record.get('flags'):
                    try:
                        record['flags'] = json.loads(record['flags'])
                    except json.JSONDecodeError:
                        record['flags'] = []
                compliance_checks.append(record)
            
            # Get recent audit trail
            cursor.execute('''
                SELECT * FROM audit_trail 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''', (user_id,))
            
            rows = cursor.fetchall()
            audit_records = []
            for row in rows:
                record = dict(zip(columns, row))
                if record.get('details'):
                    try:
                        record['details'] = json.loads(record['details'])
                    except json.JSONDecodeError:
                        record['details'] = {}
                if record.get('regulatory_flags'):
                    try:
                        record['regulatory_flags'] = json.loads(record['regulatory_flags'])
                    except json.JSONDecodeError:
                        record['regulatory_flags'] = []
                audit_records.append(record)
            
            return {
                "user_id": user_id,
                "compliance_status": "compliant" if not any(c.get('flags') for c in compliance_checks) else "flagged",
                "recent_checks": compliance_checks,
                "recent_activity": audit_records,
                "kyc_status": "verified",  # Placeholder
                "aml_status": "clear",     # Placeholder
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting compliance status: {str(e)}")
            raise Exception(f"Compliance status retrieval failed: {str(e)}")
    
    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics and statistics."""
        try:
            cursor = self.audit_db.cursor()
            
            # Get basic metrics
            cursor.execute("SELECT COUNT(*) FROM audit_trail")
            total_audit_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM compliance_checks")
            total_compliance_checks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM regulatory_reports")
            total_reports = cursor.fetchone()[0]
            
            # Get today's metrics
            today = datetime.now().date()
            cursor.execute("SELECT COUNT(*) FROM audit_trail WHERE DATE(timestamp) = ?", (today,))
            today_audit_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM compliance_checks WHERE DATE(timestamp) = ?", (today,))
            today_compliance_checks = cursor.fetchone()[0]
            
            return {
                "total_audit_records": total_audit_records,
                "total_compliance_checks": total_compliance_checks,
                "total_regulatory_reports": total_reports,
                "today_audit_records": today_audit_records,
                "today_compliance_checks": today_compliance_checks,
                "config": self.config,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting compliance metrics: {str(e)}")
            raise Exception(f"Metrics retrieval failed: {str(e)}")


class AgenticComplianceAgent(BaseAgent):
    """
    Autonomous Compliance Agent for VolexSwarm.
    
    This agent provides autonomous compliance monitoring, audit trail management,
    regulatory reporting, and compliance checks. It operates independently to ensure
    all trading activities meet regulatory requirements.
    """
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        # Provide a default LLM config if none is provided
        if llm_config is None:
            llm_config = {
                "config_list": [
                    {
                        "api_type": "openai",
                        "api_key": "dummy-key",  # Will be overridden by environment
                        "model": "gpt-4o-mini"
                    }
                ],
                "temperature": 0.7
            }
        system_message = """You are the VolexSwarm Compliance Agent, an autonomous regulatory compliance and audit management system.

Your primary responsibilities include:

1. **Trade Logging & Audit Trails**: Automatically log all trades for regulatory compliance and maintain immutable audit trails with cryptographic hashing for data integrity.

2. **Compliance Checks**: Perform comprehensive compliance checks including:
   - KYC (Know Your Customer) verification
   - AML (Anti-Money Laundering) screening
   - Suspicious activity detection
   - Daily trade limit monitoring
   - Pattern analysis for suspicious trading behavior

3. **Regulatory Reporting**: Generate automated regulatory reports for various jurisdictions and time periods, ensuring compliance with financial regulations.

4. **Compliance Monitoring**: Continuously monitor trading activities and flag potential compliance issues for review.

5. **Audit Trail Management**: Maintain detailed audit trails with filtering, search, and export capabilities for regulatory examinations.

6. **Compliance Status Tracking**: Track and report compliance status for all users and trading activities.

You operate autonomously and proactively identify compliance risks, generate required reports, and maintain regulatory compliance across all trading activities. You integrate with the broader VolexSwarm system to ensure all trading operations meet regulatory standards.

Available capabilities:
- log_trade: Log trades for audit and compliance purposes
- perform_compliance_check: Perform comprehensive compliance checks
- get_audit_trail: Retrieve audit trail with filtering and pagination
- generate_regulatory_report: Generate regulatory compliance reports
- get_compliance_status: Get compliance status for users
- get_compliance_metrics: Get compliance metrics and statistics
- get_compliance_config: Get current compliance configuration
- update_compliance_config: Update compliance configuration

Always ensure data integrity, maintain audit trails, and proactively identify compliance risks."""

        config = AgentConfig(
            name="AgenticComplianceAgent",
            system_message=system_message,
            llm_config=llm_config
        )
        super().__init__(config)
        
        # Initialize compliance manager
        self.compliance_manager = ComplianceManager(COMPLIANCE_CONFIG)
        self.db_client = None
        self.ws_client = None
        
        # Initialize infrastructure attributes for test compatibility
        self.vault_client = None
        self.openai_client = None
        
    async def initialize_infrastructure(self):
        """Initialize connections to existing infrastructure."""
        try:
            # Initialize Vault client
            from common.vault import get_vault_client, get_agent_config
            self.vault_client = get_vault_client()
            
            # Initialize database client
            from common.db import get_db_client
            self.db_client = get_db_client()
            
            # Initialize OpenAI client
            from common.openai_client import get_openai_client
            self.openai_client = get_openai_client()
            
            # Configure LLM with real API key from Vault
            if self.vault_client:
                # Get agent-specific config
                agent_config = get_agent_config("compliance")
                
                # Get OpenAI API key from the correct location
                openai_secret = self.vault_client.get_secret("openai/api_key")
                openai_api_key = None
                if openai_secret and "api_key" in openai_secret:
                    openai_api_key = openai_secret["api_key"]
                
                if openai_api_key:
                    # Update the LLM config with the real API key
                    self.config.llm_config = {
                        "config_list": [{
                            "api_type": "openai",
                            "model": "gpt-4o-mini",
                            "api_key": openai_api_key
                        }],
                        "temperature": 0.7
                    }
                    logger.info("LLM configured with Vault API key")
                else:
                    logger.warning("OpenAI API key not found in Vault")
            
            logger.info("Infrastructure initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize infrastructure: {e}")
            raise
    
    async def initialize(self):
        """Initialize the agent."""
        try:
            # Initialize database client
            self.db_client = get_db_client()
            
            # Initialize WebSocket client for real-time communication
            self.ws_client = AgentWebSocketClient("agentic_compliance")
            await self.ws_client.connect()
            
            logger.info("Agentic Compliance Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Agentic Compliance Agent: {e}")
            return False
            
    async def shutdown(self):
        """Shutdown the agent."""
        try:
            if self.ws_client:
                await self.ws_client.disconnect()
            if self.compliance_manager.audit_db:
                self.compliance_manager.audit_db.close()
            logger.info("Agentic Compliance Agent shutdown successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def log_trade(self, trade_id: str, symbol: str, side: str, quantity: float, 
                       price: float, exchange: str, order_id: str, user_id: Optional[str] = None,
                       strategy_id: Optional[str] = None, risk_assessment: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Log a trade for audit and compliance purposes."""
        try:
            request = TradeLogRequest(
                trade_id=trade_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                timestamp=datetime.now(),
                exchange=exchange,
                order_id=order_id,
                user_id=user_id,
                strategy_id=strategy_id,
                risk_assessment=risk_assessment
            )
            
            result = self.compliance_manager.log_trade(request)
            logger.info(f"Trade logged successfully: {trade_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to log trade: {str(e)}")
            raise

    async def perform_compliance_check(self, user_id: str, trade_amount: float, symbol: str, 
                                     side: str, exchange: str, kyc_status: Optional[str] = None,
                                     aml_status: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive compliance checks for a trade."""
        try:
            request = ComplianceCheckRequest(
                user_id=user_id,
                trade_amount=trade_amount,
                symbol=symbol,
                side=side,
                exchange=exchange,
                timestamp=datetime.now(),
                kyc_status=kyc_status,
                aml_status=aml_status
            )
            
            result = self.compliance_manager.perform_compliance_checks(
                request.user_id, request.trade_amount, request.symbol, request.side
            )
            logger.info(f"Compliance check completed for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to perform compliance check: {str(e)}")
            raise

    async def get_audit_trail(self, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None, user_id: Optional[str] = None,
                            symbol: Optional[str] = None, action_type: Optional[str] = None,
                            limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Retrieve audit trail with filtering and pagination."""
        try:
            request = AuditTrailRequest(
                start_date=start_date,
                end_date=end_date,
                user_id=user_id,
                symbol=symbol,
                action_type=action_type,
                limit=limit,
                offset=offset
            )
            
            result = self.compliance_manager.get_audit_trail(request)
            logger.info(f"Audit trail retrieved: {len(result.get('audit_records', []))} records")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get audit trail: {str(e)}")
            raise

    async def generate_regulatory_report(self, report_type: str, start_date: datetime, 
                                       end_date: datetime, jurisdiction: str = "US",
                                       format: str = "json") -> Dict[str, Any]:
        """Generate regulatory compliance report."""
        try:
            request = RegulatoryReportRequest(
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                jurisdiction=jurisdiction,
                format=format
            )
            
            result = self.compliance_manager.generate_regulatory_report(request)
            logger.info(f"Regulatory report generated: {result['report_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate regulatory report: {str(e)}")
            raise

    async def get_compliance_status(self, user_id: str) -> Dict[str, Any]:
        """Get compliance status for a user."""
        try:
            result = self.compliance_manager.get_compliance_status(user_id)
            logger.info(f"Compliance status retrieved for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get compliance status: {str(e)}")
            raise

    async def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics and statistics."""
        try:
            result = self.compliance_manager.get_compliance_metrics()
            logger.info("Compliance metrics retrieved")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get compliance metrics: {str(e)}")
            raise

    async def get_compliance_config(self) -> Dict[str, Any]:
        """Get current compliance configuration."""
        try:
            return {
                "config": COMPLIANCE_CONFIG,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Failed to get compliance config: {str(e)}")
            raise

    async def update_compliance_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update compliance configuration."""
        try:
            # Validate configuration
            required_keys = [
                "audit_log_retention_days", "trade_reporting_enabled", "kyc_required",
                "aml_checks_enabled", "suspicious_activity_threshold", "daily_trade_limit",
                "regulatory_jurisdiction", "reporting_frequency", "audit_trail_encryption",
                "compliance_checks_enabled"
            ]
            
            for key in required_keys:
                if key not in config:
                    raise Exception(f"Missing required config key: {key}")
            
            # Update configuration
            global COMPLIANCE_CONFIG
            COMPLIANCE_CONFIG.update(config)
            
            # Reinitialize compliance manager with new config
            self.compliance_manager = ComplianceManager(COMPLIANCE_CONFIG)
            
            logger.info(f"Compliance configuration updated: {config}")
            
            return {
                "message": "Compliance configuration updated successfully",
                "config": COMPLIANCE_CONFIG,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to update compliance configuration: {str(e)}")
            raise

    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_type": "AgenticComplianceAgent",
            "status": "active",
            "compliance_manager_ready": self.compliance_manager is not None,
            "db_connected": self.db_client is not None,
            "ws_connected": self.ws_client is not None and self.ws_client.is_connected,
            "config": COMPLIANCE_CONFIG,
            "timestamp": datetime.now()
        } 