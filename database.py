import mysql.connector
from mysql.connector import errorcode

def create_connection():
    """Create a MySQL database connection."""
    # Example configuration dictionary
    """ config = {
        'user': 'root',
        'password': '',
        'host': 'localhost',  # or your MySQL server's IP address
        'database': 'food_donation',
        'raise_on_warnings': True
    } """

    config = {
    'user': "admin",
    'password': "mysql-x23228946",
    'host': "mysql-x23228946.czknbnws0k3r.us-east-1.rds.amazonaws.com",
    'database': "mysql-x23228946",
    'raise_on_warnings': True
    }
    
    try:
        conn = mysql.connector.connect(**config)
        print("Connection successful.")
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Invalid username or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist.")
        else:
            print(f"Error: {err}")
        return None


conn = create_connection()
cur = conn.cursor()
cur.execute("update donation set status = %s where ngo_id = 0 and expiry < NOW()" ,("expired",))
conn.commit()
cur.close()


""" # Use the connection function
conn = create_connection()
if conn:
    cursor = conn.cursor()

    
    cursor.execute(create_table_query)
    print("Table created successfully.")

    # Close the cursor and connection
    cursor.close()
    conn.close() """
