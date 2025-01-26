from fastapi import FastAPI, HTTPException
from langchain.llms import HuggingFaceHub
from langchain_community.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import mysql.connector
from langgraph.graph import Graph
from langgraph.prebuilt import ToolExecutor
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",  # Your frontend's origin
    "http://localhost:8000",  # Your frontend's origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Configuration
mydb = mysql.connector.connect(
    host="localhost",
    user="root", #replace with your mysql user
    password="Sizen@123", #replace with your mysql password
    database="product_db"
)

@app.get("/api/chat")
async def chat(query: str):
    try:
        mycursor = mydb.cursor(dictionary=True)

        def get_products(query):
            sql = f"SELECT * FROM Products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%' OR brand LIKE '%{query}%' OR category LIKE '%{query}%'"
            mycursor.execute(sql)
            return mycursor.fetchall()
        
        def get_suppliers(query):
            sql = f"SELECT * FROM Suppliers WHERE name LIKE '%{query}%'"
            mycursor.execute(sql)
            return mycursor.fetchall()

        tools = [
            Tool(
                name = "Product Search",
                func=get_products,
                description="useful for when you need to answer questions about products. Input should be a search query."
            ),
            Tool(
                name="Supplier Search",
                func=get_suppliers,
                description="useful for when you need to answer questions about suppliers. Input should be a search query."
            )
        ]

        llm = HuggingFaceHub(repo_id="google/flan-t5-xl", model_kwargs={"temperature":0.5, "max_length":512})
        agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
        result = agent.run(query)

        return {"response": result}
        

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))