import pymysql

def query(query, database_name="cve_mappings"):
    db = pymysql.connect(
        host="localhost",
        user="root",
        passwd="password",
        database=database_name
    )
    
    cursor = db.cursor()
    cursor.execute(query)

    return cursor.fetchall()