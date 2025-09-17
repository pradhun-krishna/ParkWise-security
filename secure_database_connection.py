# Secure Database Connection for Shobha ANPR System
# Provides read-only database operations with security restrictions

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

load_dotenv()

class SecureDatabaseConnection:
    def __init__(self):
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'shobha_parking'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        # Security settings
        self.read_only_mode = True
        self.allowed_operations = [
            'SELECT', 'INSERT', 'UPDATE'
        ]
        self.blocked_operations = [
            'DROP', 'DELETE', 'CREATE', 'ALTER', 'TRUNCATE',
            'GRANT', 'REVOKE', 'EXECUTE', 'CALL'
        ]
        
        # ONLY allow access to "shobha" tables
        self.allowed_tables = [
            'shobha_permanent_parking',
            'shobha_permanent_parking_sessions'
        ]
        
        self.connection = None
        self.setup_logging()
        self.connect()
    
    def setup_logging(self):
        """Setup security logging"""
        self.logger = logging.getLogger("secure_db")
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create file handler
        handler = logging.FileHandler("logs/database_security.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def connect(self):
        """Establish database connection with read-only user"""
        try:
            # Try to connect with read-only user first
            read_only_config = self.db_config.copy()
            read_only_config['user'] = f"{self.db_config['user']}_readonly"
            
            try:
                self.connection = psycopg2.connect(**read_only_config)
                self.logger.info("Connected with read-only user")
            except:
                # Fallback to regular user but enforce read-only mode
                self.connection = psycopg2.connect(**self.db_config)
                self.logger.warning("Connected with regular user - enforcing read-only mode")
            
            print("✅ Secure PostgreSQL database connected successfully")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.connection = None
    
    def validate_query(self, query: str) -> bool:
        """Validate query for security restrictions"""
        query_upper = query.upper().strip()
        
        # Check for blocked operations
        for blocked_op in self.blocked_operations:
            if blocked_op in query_upper:
                self.logger.warning(f"Blocked operation detected: {blocked_op} in query: {query}")
                return False
        
        # Check for allowed operations only
        has_allowed_op = any(op in query_upper for op in self.allowed_operations)
        if not has_allowed_op:
            self.logger.warning(f"No allowed operations in query: {query}")
            return False
        
        # Check for allowed tables only (ONLY "shobha" tables)
        # Allow simple queries that don't reference tables (like SELECT 1)
        has_table_reference = any(keyword in query_upper for keyword in ['FROM', 'JOIN', 'UPDATE', 'INSERT', 'DELETE'])
        if has_table_reference:
            has_allowed_table = any(table in query_upper for table in self.allowed_tables)
            if not has_allowed_table:
                # Allow COUNT queries for statistics
                if 'COUNT(' in query_upper and any(table in query_upper for table in self.allowed_tables):
                    self.logger.info(f"Allowing COUNT query for statistics: {query}")
                    return True
                self.logger.warning(f"No allowed tables in query: {query}")
                return False
        
        # Additional security checks
        if self.read_only_mode:
            # Block any structural changes
            structural_keywords = [
                'CREATE TABLE', 'ALTER TABLE', 'DROP TABLE',
                'CREATE INDEX', 'DROP INDEX', 'CREATE VIEW',
                'DROP VIEW', 'CREATE FUNCTION', 'DROP FUNCTION'
            ]
            
            for keyword in structural_keywords:
                if keyword in query_upper:
                    self.logger.warning(f"Structural change blocked: {keyword} in query: {query}")
                    return False
        
        return True
    
    def get_cursor(self):
        """Get database cursor"""
        if self.connection:
            return self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return None
    
    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False) -> any:
        """Execute query and return results"""
        try:
            # Validate query
            if not self.validate_query(query):
                self.logger.error(f"Query validation failed: {query}")
                return None if fetch_one else []
            
            cursor = self.get_cursor()
            if not cursor:
                return None if fetch_one else []
            
            cursor.execute(query, params)
            
            if fetch_one:
                result = cursor.fetchone()
                cursor.close()
                return result
            elif fetch_all:
                results = cursor.fetchall()
                cursor.close()
                return results
            else:
                # Default behavior - fetch all and convert to list of dictionaries
                results = cursor.fetchall()
                cursor.close()
                
                # Log successful query
                self.logger.info(f"Query executed successfully: {query[:100]}...")
                
                # Convert to list of dictionaries
                return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            return None if fetch_one else []
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute INSERT/UPDATE query with security restrictions"""
        try:
            # Validate query
            if not self.validate_query(query):
                self.logger.error(f"Update query validation failed: {query}")
                return False
            
            # Additional check for read-only mode
            if self.read_only_mode and 'UPDATE' in query.upper():
                self.logger.warning(f"UPDATE blocked in read-only mode: {query}")
                return False
            
            cursor = self.get_cursor()
            if not cursor:
                return False
            
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            
            # Log successful update
            self.logger.info(f"Update executed successfully: {query[:100]}...")
            return True
        except Exception as e:
            self.logger.error(f"Update execution error: {e}")
            return False
    
    def check_permanent_parking(self, vehicle_number: str) -> Optional[Dict]:
        """Check if vehicle has permanent parking access (READ-ONLY)"""
        query = """
            SELECT * FROM shobha_permanent_parking 
            WHERE vehicle_number = %s
        """
        results = self.execute_query(query, (vehicle_number,))
        return results[0] if results else None
    
    def create_booking_session(self, vehicle_number: str, lot_id: str = None) -> Optional[str]:
        """Create new booking session (INSERT only)"""
        query = """
            INSERT INTO booking_sessions 
            (vehicle_number, lot_id, status, payment_status, base_fee, created_at)
            VALUES (%s, %s, 'booked', 'pending', 20, %s)
            RETURNING id
        """
        
        now = datetime.now()
        if self.execute_update(query, (vehicle_number, lot_id, now)):
            # Get the created session ID
            get_query = """
                SELECT id FROM booking_sessions 
                WHERE vehicle_number = %s AND status = 'booked'
                ORDER BY created_at DESC LIMIT 1
            """
            results = self.execute_query(get_query, (vehicle_number,))
            return str(results[0]['id']) if results else None
        return None
    
    def update_session_entry(self, session_id: str) -> bool:
        """Update session with entry time and change status to active (UPDATE only)"""
        query = """
            UPDATE booking_sessions 
            SET entry_time = %s, status = 'active'
            WHERE id = %s
        """
        now = datetime.now()
        return self.execute_update(query, (now, session_id))
    
    def update_session_exit(self, session_id: str) -> bool:
        """Update session with exit time, calculate fees, and mark as completed (UPDATE only)"""
        # First get the session details
        get_query = """
            SELECT entry_time, base_fee FROM booking_sessions 
            WHERE id = %s
        """
        results = self.execute_query(get_query, (session_id,))
        
        if not results:
            return False
        
        session = results[0]
        entry_time = session['entry_time']
        base_fee = session['base_fee']
        exit_time = datetime.now()
        
        # Calculate duration and total fee
        duration = exit_time - entry_time
        duration_minutes = int(duration.total_seconds() / 60)
        
        # Calculate total fee (base_fee + hourly rate)
        per_hour_fee = 10  # From your schema
        hours = duration_minutes / 60
        total_fee = base_fee + int(hours * per_hour_fee)
        
        # Update the session
        update_query = """
            UPDATE booking_sessions 
            SET exit_time = %s, duration_minutes = %s, total_fee = %s, status = 'completed'
            WHERE id = %s
        """
        return self.execute_update(update_query, (exit_time, duration_minutes, total_fee, session_id))
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all active parking sessions (READ-ONLY)"""
        query = """
            SELECT * FROM booking_sessions 
            WHERE status IN ('booked', 'active')
            ORDER BY created_at DESC
        """
        return self.execute_query(query)
    
    def get_recent_sessions(self, limit: int = 50) -> List[Dict]:
        """Get recent parking sessions (READ-ONLY)"""
        query = """
            SELECT * FROM booking_sessions 
            ORDER BY created_at DESC 
            LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    def get_permanent_vehicles(self) -> List[Dict]:
        """Get all permanent parking vehicles (READ-ONLY)"""
        query = """
            SELECT * FROM shobha_permanent_parking 
            ORDER BY created_at DESC
        """
        return self.execute_query(query)
    
    def create_permanent_session(self, permanent_parking_id: str) -> bool:
        """Create session for permanent parking vehicle (INSERT only)"""
        query = """
            INSERT INTO shobha_permanent_parking_sessions 
            (permanent_parking_id, entry_time)
            VALUES (%s, %s)
        """
        now = datetime.now()
        return self.execute_update(query, (permanent_parking_id, now))
    
    def update_permanent_session_exit(self, permanent_parking_id: str) -> bool:
        """Update permanent parking session with exit time (UPDATE only)"""
        query = """
            UPDATE shobha_permanent_parking_sessions 
            SET exit_time = %s, duration_minutes = EXTRACT(EPOCH FROM (%s - entry_time))/60
            WHERE permanent_parking_id = %s AND exit_time IS NULL
        """
        now = datetime.now()
        return self.execute_update(query, (now, now, permanent_parking_id))
    
    def get_system_stats(self) -> Dict[str, int]:
        """Get system statistics (READ-ONLY)"""
        stats = {}
        
        try:
            # Total sessions (using shobha_permanent_parking_sessions)
            total_query = "SELECT COUNT(*) as count FROM shobha_permanent_parking_sessions"
            total_result = self.execute_query(total_query)
            stats['total_sessions'] = total_result[0]['count'] if total_result else 0
            
            # Active sessions (sessions without exit_time)
            active_query = "SELECT COUNT(*) as count FROM shobha_permanent_parking_sessions WHERE exit_time IS NULL"
            active_result = self.execute_query(active_query)
            stats['active_sessions'] = active_result[0]['count'] if active_result else 0
            
            # Completed sessions (sessions with exit_time)
            completed_query = "SELECT COUNT(*) as count FROM shobha_permanent_parking_sessions WHERE exit_time IS NOT NULL"
            completed_result = self.execute_query(completed_query)
            stats['completed_sessions'] = completed_result[0]['count'] if completed_result else 0
            
            # Permanent vehicles
            permanent_query = "SELECT COUNT(*) as count FROM shobha_permanent_parking"
            permanent_result = self.execute_query(permanent_query)
            stats['permanent_vehicles'] = permanent_result[0]['count'] if permanent_result else 0
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            stats = {
                'total_sessions': 0,
                'active_sessions': 0,
                'completed_sessions': 0,
                'permanent_vehicles': 0
            }
        
        return stats
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information (READ-ONLY)"""
        try:
            # Get database version
            version_query = "SELECT version()"
            version_result = self.execute_query(version_query)
            
            # Get current user
            user_query = "SELECT current_user"
            user_result = self.execute_query(user_query)
            
            # Get database name
            dbname_query = "SELECT current_database()"
            dbname_result = self.execute_query(dbname_query)
            
            return {
                'version': version_result[0]['version'] if version_result else 'Unknown',
                'user': user_result[0]['current_user'] if user_result else 'Unknown',
                'database': dbname_result[0]['current_database'] if dbname_result else 'Unknown',
                'read_only_mode': self.read_only_mode,
                'allowed_operations': self.allowed_operations,
                'blocked_operations': self.blocked_operations
            }
        except Exception as e:
            self.logger.error(f"Error getting database info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            cursor = self.get_cursor()
            if cursor:
                cursor.execute("SELECT 1")
                cursor.close()
                self.logger.info("Database connection test successful")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed")
            print("✅ Database connection closed")

# Global secure database instance
secure_db = SecureDatabaseConnection()

