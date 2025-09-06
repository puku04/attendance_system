import mysql.connector
from mysql.connector import Error
from config import Config
import logging

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.config = {
            'host': Config.MYSQL_HOST,
            'database': Config.MYSQL_DB,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'charset': Config.MYSQL_CHARSET,
            'autocommit': True
        }
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                return True
        except Error as e:
            logging.error(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """Execute a query with optional parameters"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                affected_rows = cursor.rowcount
                last_id = cursor.lastrowid
                cursor.close()
                return {'affected_rows': affected_rows, 'last_id': last_id}
                
        except Error as e:
            logging.error(f"Query execution error: {e}")
            return None
    
    def execute_many(self, query, params_list):
        """Execute multiple queries with parameter lists"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
            
        except Error as e:
            logging.error(f"Bulk query execution error: {e}")
            return 0

# Global database instance
db = DatabaseManager()
