import sys
sys.path.append("../src/llm/")
import pypyodbc as odbc
import csv
import dotenv
import load_dotenv
dotenv.load_dotenv(dotenv.find_dotenv())

from llm_manager import LLMManager


server = 'tcp:hackaton-gr9-sqlserveri10lm.database.windows.net,1433'
database ='hackaton-gr9-sqldb'
username ='hacksqlusr012993'
password = 'hacksqlusrP@ssw00rd'

connect_str = 'Driver={ODBC Driver 18 for SQL Server};Server='+server+';Database='+database+';Uid='+username+';Pwd='+password+';Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

class SQLQuery:
    def __init__(self) -> None:
        self.server = 'tcp:hackaton-gr9-sqlserveri10lm.database.windows.net,1433'
        self.database ='hackaton-gr9-sqldb'
        self.username ='hacksqlusr012993'
        self.password = 'hacksqlusrP@ssw00rd'
        self.connect_str = 'Driver={ODBC Driver 18 for SQL Server};Server='+self.server+';Database='+self.database+';Uid='+self.username+';Pwd='+self.password+';Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        self.cursor = self.connect()
        self.llm_descriptor = LLMManager()
        self.schemas_names = [self.get_schemas_names()[1]]

    def connect(self):
        conn = odbc.connect(self.connect_str)
        cursor = conn.cursor()
        return cursor

    def get_schema(self, table_name):
        sql_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        """
        self.cursor.execute(sql_query)
        schema = self.cursor.fetchall()
        return schema

    def get_constraints(self, table):
        sql_query = f"""
    SELECT
        tc.constraint_type,
        tc.constraint_name,
        kcu.column_name
    FROM
        information_schema.table_constraints AS tc
    JOIN
        information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
        AND tc.table_name = kcu.table_name
    LEFT JOIN
        information_schema.constraint_column_usage AS ccu
        ON tc.constraint_name = ccu.constraint_name
        AND tc.table_schema = ccu.table_schema
    WHERE
        tc.table_name = '{table}'
    ORDER BY
        tc.constraint_type, kcu.column_name;
        """
        self.cursor.execute(sql_query)
        constraints = self.cursor.fetchall()
        print("sth: ",constraints)
        return constraints

    def get_schemas_names(self):
        sql_query = f'''
        SELECT 
            TABLE_SCHEMA 
        FROM 
            [hackaton-gr9-sqldb].INFORMATION_SCHEMA.TABLES
        WHERE 
            TABLE_TYPE = 'BASE TABLE';
        '''
        self.cursor.execute(sql_query)
        foreign_keys = self.cursor.fetchall()
        return [ele[0] for ele in list(set(foreign_keys))]
    
    def get_foreign_keys(self, table_name):
        sql_query = f"""
        SELECT
            ccu.column_name AS referenced_column
        FROM 
            information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
            AND tc.table_name = kcu.table_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        WHERE 
            tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = '{table_name}';
        """
        self.cursor.execute(sql_query)
        foreign_keys = self.cursor.fetchall()
        return foreign_keys

    def get_table_names(self): 
        tables=[]
        s_names=[]
        for schema_name in self.schemas_names:
            sql_query = f"""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema_name}'
            """
            self.cursor.execute(sql_query)
            tables.append(self.cursor.fetchall())
            s_names.extend([schema_name] * len(tables[-1]))

        return s_names, [names[0] for table in tables for names in table]


    def load_csv_data(self, data):
        print("DANE: ",data)
        with open('data/products.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write the header
            writer.writerow(["desc","schema","table_name","schema_name",'neighbours', 'constraints' , 'access'])
            # Write the rows
            writer.writerows([single for single in data])


    def main(self):
        schema_names, tables = self.get_table_names()
        final_data = []
        print("tabele do csv: ", tables)
        print("schematy do tabel: ", schema_names)
        for schema_name, table_name in zip(schema_names, tables):
            schema = self.get_schema(table_name)
            foreign_keys = self.get_foreign_keys(table_name)
            constraints = self.get_constraints(table_name)
            description = self.llm_descriptor.generate_table_description({"columns":schema})
            final_data.append([description,schema,table_name, schema_name,foreign_keys,constraints, 1])

        self.load_csv_data(final_data)

if __name__ == '__main__':
    sqler = SQLQuery()
    sqler.main()

