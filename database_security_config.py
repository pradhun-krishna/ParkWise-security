# Database Security Configuration for Shobha ANPR System
# Defines security policies and restrictions

class DatabaseSecurityConfig:
    def __init__(self):
        # Security mode settings
        self.read_only_mode = True
        self.enable_audit_logging = True
        self.enable_query_validation = True
        self.enable_connection_monitoring = True
        
        # Allowed operations (only these are permitted)
        self.allowed_operations = [
            'SELECT',      # Read data
            'INSERT',      # Add new records
            'UPDATE'       # Modify existing records
        ]
        
        # Blocked operations (these are completely forbidden)
        self.blocked_operations = [
            'DROP',        # Delete tables/columns
            'DELETE',      # Remove records
            'CREATE',      # Create new structures
            'ALTER',       # Modify table structure
            'TRUNCATE',    # Clear table data
            'GRANT',       # Grant permissions
            'REVOKE',      # Revoke permissions
            'EXECUTE',     # Execute stored procedures
            'CALL',        # Call functions
            'REPLACE',     # Replace data
            'MERGE',       # Merge operations
            'UPSERT'       # Upsert operations
        ]
        
        # Blocked keywords (additional security)
        self.blocked_keywords = [
            'CREATE TABLE', 'ALTER TABLE', 'DROP TABLE',
            'CREATE INDEX', 'DROP INDEX', 'CREATE VIEW',
            'DROP VIEW', 'CREATE FUNCTION', 'DROP FUNCTION',
            'CREATE PROCEDURE', 'DROP PROCEDURE', 'CREATE TRIGGER',
            'DROP TRIGGER', 'CREATE SCHEMA', 'DROP SCHEMA',
            'CREATE DATABASE', 'DROP DATABASE', 'CREATE USER',
            'DROP USER', 'CREATE ROLE', 'DROP ROLE',
            'GRANT', 'REVOKE', 'EXECUTE', 'CALL',
            'TRUNCATE', 'DELETE FROM', 'REPLACE INTO',
            'MERGE INTO', 'UPSERT INTO'
        ]
        
        # Allowed tables (only these can be accessed)
        self.allowed_tables = [
            'booking_sessions',
            'shobha_permanent_parking',
            'shobha_permanent_parking_sessions',
            'parking_lots'
        ]
        
        # Blocked tables (these cannot be accessed)
        self.blocked_tables = [
            'pg_user', 'pg_group', 'pg_shadow', 'pg_authid',
            'pg_roles', 'pg_database', 'pg_tablespace',
            'pg_namespace', 'pg_class', 'pg_attribute',
            'pg_index', 'pg_constraint', 'pg_trigger',
            'pg_proc', 'pg_type', 'pg_operator',
            'pg_aggregate', 'pg_am', 'pg_amop',
            'pg_amproc', 'pg_cast', 'pg_collation',
            'pg_conversion', 'pg_depend', 'pg_description',
            'pg_enum', 'pg_event_trigger', 'pg_extension',
            'pg_foreign_data_wrapper', 'pg_foreign_server',
            'pg_foreign_table', 'pg_inherits', 'pg_init_privs',
            'pg_language', 'pg_largeobject', 'pg_largeobject_metadata',
            'pg_matviews', 'pg_opclass', 'pg_operator',
            'pg_opfamily', 'pg_partitioned_table', 'pg_pltemplate',
            'pg_policy', 'pg_publication', 'pg_publication_rel',
            'pg_publication_tables', 'pg_range', 'pg_rewrite',
            'pg_seclabel', 'pg_sequence', 'pg_shdepend',
            'pg_shdescription', 'pg_shseclabel', 'pg_stat_archiver',
            'pg_stat_bgwriter', 'pg_stat_database', 'pg_stat_database_conflicts',
            'pg_stat_database_conflicts', 'pg_stat_user_functions',
            'pg_stat_user_indexes', 'pg_stat_user_tables',
            'pg_stat_user_tables', 'pg_stat_wal_receiver',
            'pg_stat_wal_sender', 'pg_stat_xact_user_functions',
            'pg_stat_xact_user_indexes', 'pg_stat_xact_user_tables',
            'pg_stat_xact_user_tables', 'pg_statistic',
            'pg_statistic_ext', 'pg_subscription', 'pg_subscription_rel',
            'pg_tablespace', 'pg_transform', 'pg_trigger',
            'pg_ts_config', 'pg_ts_config_map', 'pg_ts_dict',
            'pg_ts_parser', 'pg_ts_template', 'pg_type',
            'pg_user_mapping', 'pg_views', 'pg_publication_tables',
            'pg_stat_activity', 'pg_stat_replication',
            'pg_stat_subscription', 'pg_stat_wal_receiver',
            'pg_stat_wal_sender', 'pg_stat_xact_user_functions',
            'pg_stat_xact_user_indexes', 'pg_stat_xact_user_tables',
            'pg_stat_xact_user_tables', 'pg_statistic',
            'pg_statistic_ext', 'pg_subscription', 'pg_subscription_rel',
            'pg_tablespace', 'pg_transform', 'pg_trigger',
            'pg_ts_config', 'pg_ts_config_map', 'pg_ts_dict',
            'pg_ts_parser', 'pg_ts_template', 'pg_type',
            'pg_user_mapping', 'pg_views'
        ]
        
        # Security policies
        self.security_policies = {
            'max_query_length': 1000,  # Maximum query length
            'max_results': 1000,       # Maximum results per query
            'query_timeout': 30,       # Query timeout in seconds
            'connection_timeout': 300,  # Connection timeout in seconds
            'max_connections': 5,      # Maximum concurrent connections
            'audit_retention_days': 30  # Audit log retention
        }
        
        # Audit settings
        self.audit_settings = {
            'log_all_queries': True,
            'log_failed_queries': True,
            'log_successful_queries': True,
            'log_connection_attempts': True,
            'log_security_violations': True,
            'log_performance_issues': True
        }
    
    def is_operation_allowed(self, operation: str) -> bool:
        """Check if an operation is allowed"""
        return operation.upper() in self.allowed_operations
    
    def is_operation_blocked(self, operation: str) -> bool:
        """Check if an operation is blocked"""
        return operation.upper() in self.blocked_operations
    
    def is_keyword_blocked(self, query: str) -> bool:
        """Check if query contains blocked keywords"""
        query_upper = query.upper()
        for keyword in self.blocked_keywords:
            if keyword in query_upper:
                return True
        return False
    
    def is_table_allowed(self, table_name: str) -> bool:
        """Check if a table is allowed to be accessed"""
        return table_name.lower() in self.allowed_tables
    
    def is_table_blocked(self, table_name: str) -> bool:
        """Check if a table is blocked from access"""
        return table_name.lower() in self.blocked_tables
    
    def validate_query_security(self, query: str) -> tuple[bool, str]:
        """Validate query against security policies"""
        query_upper = query.upper().strip()
        
        # Check query length
        if len(query) > self.security_policies['max_query_length']:
            return False, "Query too long"
        
        # Check for blocked keywords
        if self.is_keyword_blocked(query):
            return False, "Query contains blocked keywords"
        
        # Check for blocked operations
        for blocked_op in self.blocked_operations:
            if blocked_op in query_upper:
                return False, f"Blocked operation: {blocked_op}"
        
        # Check for allowed operations
        has_allowed_op = any(op in query_upper for op in self.allowed_operations)
        if not has_allowed_op:
            return False, "No allowed operations found"
        
        # Check for table access
        for table in self.allowed_tables:
            if table in query_upper:
                if not self.is_table_allowed(table):
                    return False, f"Table access denied: {table}"
        
        return True, "Query validated successfully"
    
    def get_security_report(self) -> dict:
        """Get security configuration report"""
        return {
            'read_only_mode': self.read_only_mode,
            'allowed_operations': self.allowed_operations,
            'blocked_operations': self.blocked_operations,
            'allowed_tables': self.allowed_tables,
            'blocked_tables': self.blocked_tables,
            'security_policies': self.security_policies,
            'audit_settings': self.audit_settings
        }

# Global security configuration
security_config = DatabaseSecurityConfig()


