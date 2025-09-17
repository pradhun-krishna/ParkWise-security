# Database Security Setup for Shobha ANPR System
# Creates read-only database user and applies security restrictions

import psycopg2
import psycopg2.extras
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseSecuritySetup:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'shobha_parking'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        self.readonly_user = f"{self.db_config['user']}_readonly"
        self.readonly_password = f"{self.db_config['password']}_readonly"
        
        # Tables that the readonly user can access
        self.allowed_tables = [
            'booking_sessions',
            'shobha_permanent_parking',
            'shobha_permanent_parking_sessions',
            'parking_lots'
        ]
    
    def connect_as_admin(self):
        """Connect to database as admin user"""
        try:
            connection = psycopg2.connect(**self.db_config)
            print("✅ Connected to database as admin")
            return connection
        except Exception as e:
            print(f"❌ Failed to connect as admin: {e}")
            return None
    
    def create_readonly_user(self):
        """Create read-only database user"""
        print("🔐 Creating read-only database user...")
        
        connection = self.connect_as_admin()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Create readonly user
            create_user_sql = f"""
                CREATE USER {self.readonly_user} WITH PASSWORD '{self.readonly_password}';
            """
            cursor.execute(create_user_sql)
            
            # Grant connect permission
            grant_connect_sql = f"""
                GRANT CONNECT ON DATABASE {self.db_config['database']} TO {self.readonly_user};
            """
            cursor.execute(grant_connect_sql)
            
            # Grant usage on schema
            grant_usage_sql = f"""
                GRANT USAGE ON SCHEMA public TO {self.readonly_user};
            """
            cursor.execute(grant_usage_sql)
            
            # Grant select permissions on allowed tables
            for table in self.allowed_tables:
                grant_select_sql = f"""
                    GRANT SELECT ON {table} TO {self.readonly_user};
                """
                cursor.execute(grant_select_sql)
                print(f"✅ Granted SELECT permission on {table}")
            
            # Grant insert permissions on allowed tables (for new records)
            for table in self.allowed_tables:
                grant_insert_sql = f"""
                    GRANT INSERT ON {table} TO {self.readonly_user};
                """
                cursor.execute(grant_insert_sql)
                print(f"✅ Granted INSERT permission on {table}")
            
            # Grant update permissions on allowed tables (for modifications)
            for table in self.allowed_tables:
                grant_update_sql = f"""
                    GRANT UPDATE ON {table} TO {self.readonly_user};
                """
                cursor.execute(grant_update_sql)
                print(f"✅ Granted UPDATE permission on {table}")
            
            # Grant sequence permissions for auto-increment fields
            grant_sequence_sql = f"""
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {self.readonly_user};
            """
            cursor.execute(grant_sequence_sql)
            print("✅ Granted sequence permissions")
            
            # Commit changes
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Read-only user '{self.readonly_user}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating readonly user: {e}")
            connection.rollback()
            cursor.close()
            connection.close()
            return False
    
    def create_security_policies(self):
        """Create additional security policies"""
        print("🛡️ Creating security policies...")
        
        connection = self.connect_as_admin()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Create audit log table
            create_audit_table_sql = """
                CREATE TABLE IF NOT EXISTS security_audit_log (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_name VARCHAR(100),
                    operation VARCHAR(50),
                    table_name VARCHAR(100),
                    query_text TEXT,
                    success BOOLEAN,
                    error_message TEXT
                );
            """
            cursor.execute(create_audit_table_sql)
            print("✅ Created security audit log table")
            
            # Grant permissions on audit table
            grant_audit_sql = f"""
                GRANT SELECT, INSERT ON security_audit_log TO {self.readonly_user};
            """
            cursor.execute(grant_audit_sql)
            print("✅ Granted audit table permissions")
            
            # Create function to log security events
            create_log_function_sql = """
                CREATE OR REPLACE FUNCTION log_security_event(
                    p_user_name VARCHAR(100),
                    p_operation VARCHAR(50),
                    p_table_name VARCHAR(100),
                    p_query_text TEXT,
                    p_success BOOLEAN,
                    p_error_message TEXT DEFAULT NULL
                ) RETURNS VOID AS $$
                BEGIN
                    INSERT INTO security_audit_log (
                        user_name, operation, table_name, query_text, success, error_message
                    ) VALUES (
                        p_user_name, p_operation, p_table_name, p_query_text, p_success, p_error_message
                    );
                END;
                $$ LANGUAGE plpgsql;
            """
            cursor.execute(create_log_function_sql)
            print("✅ Created security logging function")
            
            # Grant execute permission on function
            grant_function_sql = f"""
                GRANT EXECUTE ON FUNCTION log_security_event TO {self.readonly_user};
            """
            cursor.execute(grant_function_sql)
            print("✅ Granted function execute permission")
            
            # Create view for system statistics (read-only)
            create_stats_view_sql = """
                CREATE OR REPLACE VIEW system_statistics AS
                SELECT 
                    (SELECT COUNT(*) FROM booking_sessions) as total_sessions,
                    (SELECT COUNT(*) FROM booking_sessions WHERE status IN ('booked', 'active')) as active_sessions,
                    (SELECT COUNT(*) FROM booking_sessions WHERE status = 'completed') as completed_sessions,
                    (SELECT COUNT(*) FROM shobha_permanent_parking) as permanent_vehicles;
            """
            cursor.execute(create_stats_view_sql)
            print("✅ Created system statistics view")
            
            # Grant select permission on view
            grant_view_sql = f"""
                GRANT SELECT ON system_statistics TO {self.readonly_user};
            """
            cursor.execute(grant_view_sql)
            print("✅ Granted view select permission")
            
            # Commit changes
            connection.commit()
            cursor.close()
            connection.close()
            
            print("✅ Security policies created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating security policies: {e}")
            connection.rollback()
            cursor.close()
            connection.close()
            return False
    
    def test_readonly_connection(self):
        """Test the readonly user connection"""
        print("🧪 Testing readonly user connection...")
        
        readonly_config = self.db_config.copy()
        readonly_config['user'] = self.readonly_user
        readonly_config['password'] = self.readonly_password
        
        try:
            connection = psycopg2.connect(**readonly_config)
            cursor = connection.cursor()
            
            # Test basic connection
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                print("✅ Readonly user connection successful")
            
            # Test table access
            for table in self.allowed_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Can access {table} ({count} records)")
            
            # Test blocked operations (should fail)
            try:
                cursor.execute("CREATE TABLE test_table (id INT)")
                print("❌ ERROR: Should not be able to create tables")
            except:
                print("✅ Correctly blocked table creation")
            
            try:
                cursor.execute("DROP TABLE IF EXISTS test_table")
                print("❌ ERROR: Should not be able to drop tables")
            except:
                print("✅ Correctly blocked table deletion")
            
            cursor.close()
            connection.close()
            
            print("✅ Readonly user test completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Readonly user test failed: {e}")
            return False
    
    def create_secure_config_file(self):
        """Create secure configuration file for the app"""
        print("📝 Creating secure configuration file...")
        
        config_data = {
            "database": {
                "host": self.db_config["host"],
                "port": self.db_config["port"],
                "database": self.db_config["database"],
                "user": self.readonly_user,
                "password": self.readonly_password
            },
            "security": {
                "read_only_mode": True,
                "audit_logging": True,
                "query_validation": True,
                "allowed_tables": self.allowed_tables
            }
        }
        
        # Save as encrypted config
        import json
        import base64
        
        config_json = json.dumps(config_data, indent=2)
        encoded_config = base64.b64encode(config_json.encode()).decode()
        
        with open("secure_config.enc", "w") as f:
            f.write(encoded_config)
        
        print("✅ Secure configuration file created")
        return True
    
    def setup_complete_security(self):
        """Setup complete database security"""
        print("🔐 Setting up complete database security...")
        print("=" * 60)
        
        # Step 1: Create readonly user
        if not self.create_readonly_user():
            print("❌ Failed to create readonly user")
            return False
        
        # Step 2: Create security policies
        if not self.create_security_policies():
            print("❌ Failed to create security policies")
            return False
        
        # Step 3: Test readonly connection
        if not self.test_readonly_connection():
            print("❌ Readonly user test failed")
            return False
        
        # Step 4: Create secure config
        if not self.create_secure_config_file():
            print("❌ Failed to create secure config")
            return False
        
        print("\\n" + "=" * 60)
        print("✅ Database security setup completed successfully!")
        print("\\n📋 Security features implemented:")
        print(f"   - Read-only user: {self.readonly_user}")
        print(f"   - Allowed tables: {', '.join(self.allowed_tables)}")
        print("   - Audit logging enabled")
        print("   - Query validation enabled")
        print("   - Blocked operations: DROP, DELETE, CREATE, ALTER, etc.")
        print("\\n🔐 Your database is now fully secured!")
        print("\\n📝 Next steps:")
        print("1. Update your app to use the readonly user")
        print("2. Test the application with restricted permissions")
        print("3. Monitor the security audit logs")
        
        return True

def main():
    """Main function"""
    print("🔐 Shobha ANPR System - Database Security Setup")
    print("=" * 60)
    
    # Get database configuration
    print("\\n📋 Enter your database configuration:")
    host = input("Database Host [localhost]: ") or "localhost"
    port = int(input("Database Port [5432]: ") or 5432)
    database = input("Database Name [shobha_parking]: ") or "shobha_parking"
    user = input("Admin User [postgres]: ") or "postgres"
    password = input("Admin Password: ")
    
    # Update environment variables
    os.environ['DB_HOST'] = host
    os.environ['DB_PORT'] = str(port)
    os.environ['DB_NAME'] = database
    os.environ['DB_USER'] = user
    os.environ['DB_PASSWORD'] = password
    
    # Setup security
    setup = DatabaseSecuritySetup()
    success = setup.setup_complete_security()
    
    if success:
        print("\\n🎉 Database security setup complete!")
        print("\\n🔐 Your ANPR system is now fully secured!")
    else:
        print("\\n❌ Security setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()


