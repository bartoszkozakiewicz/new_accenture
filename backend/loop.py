import sys

sys.path.append("../src/llm/")
sys.path.append("../src/milvus_next/")
sys.path.append("../")
sys.path.append("/Users/bartek/Documents/ai_persp/nowy/accenture-hackathon/src/milvus_next/milvus_store.py")
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import dotenv
import pypyodbc
dotenv.load_dotenv(dotenv.find_dotenv())
from milvus_store import MilvusStoreWithClient
from sql_to_vs import SQLQuery
from langchain.agents import Tool
from langchain.agents import initialize_agent
from langchain.agents import AgentType


class Sqlagent():
    def __init__(self, collection_name: str):
        self.llm = ChatOpenAI()
        self.milvus_store = MilvusStoreWithClient()
        self.db_name = 'hackaton-gr9-sqldb'
        self.COLLECTION_NAME = collection_name
        self.schema = None
        self.query = 'Tell me about products.'
        self.prompt = ChatPromptTemplate.from_template("""Based on the table schema name, table name, schema below,  tabels related, constraints write a SQL query that would answer the user's question:
        {schema}
        Question: {question}
        Return only sql query, nothing all.
        You always have to add [hackaton-gr9-sqldb]. before schema name, when you select from that schema, for example: SELECT * FROM [hackaton-gr9-sqldb].SalesLT.vGetAllCategories
        where in this example name of the schema is SalesLT.     

        SQL Query:""")
        self.prompt2 = ChatPromptTemplate.from_template("""Based on the table schema below, question, sql query, and sql response, write a natural language response:
        {schema}
        Question: {question}
        SQL Query: {query}
        SQL Response: {response}""")

        self.cursor = SQLQuery().connect()
      
      
    def vs_search(self, *args, **kwargs):
        print("Received args:", args)
        print("Received kwargs:", kwargs)
        schema = self.milvus_store.hybrid_search(collection_name=self.COLLECTION_NAME, query=self.query)
        print("searched schema", schema)
        return schema

    def schema_chain(self, *args, **kwargs):
        chain = RunnablePassthrough.assign(schema=self.vs_search) | self.prompt | self.llm | StrOutputParser()
        return chain

    def run_query(self, query: str, *args, **kwargs):
        cursor = self.cursor
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            # print("---------------------")
            # print("---------------------")
            # print("---------------------")
            # print("result: ", result)
            # print("---------------------")
            # print("---------------------")
            cursor.close()
            return result
        except pypyodbc.Error as e:
            cursor.close()
            return str(e)

    def full_chain(self):
        tools = [
            Tool(
                name="SQL Query",
                func=self.run_query,
                description="Execute an SQL query against the database."
            )
        ]

        agent = initialize_agent(tools, self.llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                                 verbose=True)

        def iterative_query(vars):
            query = vars["query"]
            response = self.run_query(query)
            iteration = 0
            while isinstance(response, str) and "error" in response.lower():
                print(f"Error encountered: {response}")
                print("Attempting to refine the query...")
                refined_query = agent.run(
                    f"The following SQL query encountered an error: {query}\nError message: {response}\nPlease refine the query to resolve the error.")
                query = refined_query
                response = self.run_query(query)
                iteration += 1
                if iteration >= 2:
                    raise ValueError("Failed to generate a valid SQL query after 5 iterations.")
            return response

        chain = RunnablePassthrough.assign(query=self.schema_chain).assign(schema=self.vs_search,
                                                                           response=iterative_query) | self.prompt2 | self.llm
        return chain
    
    def get_answer(self, user_question: str):
        try:
            answer = self.schema_chain().invoke({"question": user_question})
            print("answer: ", answer)
            full_answer = self.full_chain().invoke({"question": user_question})
            print("full_answer: ", full_answer)
            return full_answer
        except ValueError as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    user_question = 'Give information about products'
    agent = Sqlagent(collection_name="tests")
    try:
        answer = agent.schema_chain().invoke({"question": user_question})
        print("answer: ", answer)
        full_answer = agent.full_chain().invoke({"question": user_question})
        print("full_answer: ", full_answer)
    except ValueError as e:
        print(f"Error: {str(e)}")
