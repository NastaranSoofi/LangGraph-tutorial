## UV Commands
Working with a single script file:

Commands for adding dependencies:
uv init --script script.py --python 3.8
uv add --script script.py "rich"
uv add --script script.py "requests"
uv run script.py

Command for using a dependency everytime we are running the script:
uv run --with rich --python 3.8 script.py
uv run --with rich --with requests --python 3.8 script.py

General commands:
uv python find 3.9
uv run --python 3.9 script.py
uv run script.py
arch
uname -m
uv python install 3.8
uv python list
pip install uv



Working with a python Project (Not just a script)
uv init --> terminal output: Initialized project `langgraph-tutorial`
uv run python script.py


To add dependencies manually:
manually add them into dependencies = [] in pyproject.toml
and then command: uv sync or  uv sync --reinstall


Note: I tried to add and import pygame. To run this with uv:
  uv run python script.py   # works reliably, we are explicitly calling the project .venv python
  uv run script.py          # only works if file has a shebang (#!/usr/bin/env python3), might not use the right python interpreter
Or activate the venv:
  source .venv/bin/activate && command:  python script.py


Making a new lock file command: uv lock
Removing dependencies: uv remove
Dependency removal with uv:
- If listed in pyproject.toml → uv remove <pkg> && uv sync
- If only stuck in lock → uv lock --recreate && uv sync --reinstall



# LangGraph Tutorial
uv init . (initialize in current directory)

### dependencies that we need
uv venv --python 3.13 --> Activate with: source .venv/bin/activate
uv add python-dotenv
uv add langgraph
uv add "langchain[anthropic]"
uv add ipykernel (we will use for something like Jupyter Notebook)

Now we can open our main.py file
#### also we are going to create a new file called .env file. 
this file is going to store an environment variable that will allow us to store the key for whatever the LLM we are using.
we can use any LLM.
For example Claude or entropic.
or getting API token from openAI GPT, deepSeek, ..
or use llama locally

Claude works pretty well here so we will start with Claude.


### Steps:
1. writing environment variable in .env file
ANTHROPIC_API_KEY=
to get the API key, we will go to anthropic console website. It is a paid model.
2. main.py file:
from dotenv import load_dotenv
load_dotenv() --> it is going to load the API key variable from .env file
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
form langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
3. initializeing LLM:
llm = init_chat_model(
    "anthropic:claude-3-5-sonnet-latest"
   )

4. Setting up State for our Graph: we are gonna make a class and call is State:
-We specify the state that we want our model and our agent system have access to. This is going to control the flow of our application
class State(TypedDict):
    messages: Annotated[list, add_messages] 
This means messages are going to be of type list. and whenever we want to change the messages we call a function called add_messages importer from langgraph to essentially add a new message to this list. (helps keep track of all the messages)
so the message that we say for example, user message and then the message that LLM gives back, assistant message,..
So we use Annotated[ a valid type, function for how we want to modify this type] --> for adding context-specific metadata to a type
we can put other things in the State too but  for now just messages for storing the messages

5. Define graph builder: it works using the State class. 
The graph represents our AI agent.
graph_builder = StateGraph(State)
6. Building nodes: We should figure out what the nodes are gonna be in our graph
To make a node, you simply make a function:
def chatot(state: State): --> The node is always going to be taking in the State
    return {"messages": [llm.invoke(state["messages"])]
it is going to return essentially a modification to the state. (return the next state that we'll have in the graph)
meaning: For this node, we are taking in the current state and then we return new state that contains new messages in form of list [llm.invoke(current messages)] 
when you invoke the llm it just means you're calling. we wrap the response in a list. 
And the way it works is it is simply going to add it into state because of the add_messages function defined in State class
So when we return something, it matches that State dictionary. 
since we have defined how we want to modify this state, this new message, whatever the llm returns, will simply get added to State
And that was our first node.
7. Register node in our graph in order to use the node:
graph_builder.add_node("chatbot", chatbot)
give the node some string name and then a function(in this case chatbot that we defined)
8. START node and END node: in order for our graph to work. so we need to connect the node to start and end nodes
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
9. graph = graph_builder.compile() --> to convert it to something runnable
10. Running the graph: 
user_input = input("Enter a message: ")
state = graph.invoke({"messages": [{"role": "user", "content": user_input}]})
11. print(state["messages"][-1].content)
because all of the messages have role and content and in this case we are interested in the content
and -1 because we want to grab the last message that is coming out of our llm.





# Setting up Phoenix Traces:

### 1) Install tracing deps in your project (use your venv/uv)
uv add arize-phoenix openinference-instrumentation-langchain opentelemetry-sdk opentelemetry-exporter-otlp

### run this in a separate terminal:
 uv run phoenix serve

### put this in main.py code:
from phoenix.otel import register
register(project_name="langgraph-tutorial", auto_instrument=True)



# But in this set up the traces are gone if you close the terminal. So here is an option for storing the traces:

### create docker-compose.yml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-phoenix}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-phoenix}
      POSTGRES_DB: ${POSTGRES_DB:-phoenix}
    volumes:
      - ./pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-phoenix} -d ${POSTGRES_DB:-phoenix}"]
      interval: 5s
      timeout: 3s
      retries: 10

  phoenix:
    image: arizephoenix/phoenix:latest
    depends_on:
      db:
        condition: service_healthy
    environment:
      # Either key usually works depending on version; pick one:
      PHOENIX_SQL_DATABASE_URL: postgresql://${POSTGRES_USER:-phoenix}:${POSTGRES_PASSWORD:-phoenix}@db:5432/${POSTGRES_DB:-phoenix}
      # DATABASE_URL: postgresql://${POSTGRES_USER:-phoenix}:${POSTGRES_PASSWORD:-phoenix}@db:5432/${POSTGRES_DB:-phoenix}
      PHOENIX_HOST: 0.0.0.0
      PHOENIX_PORT: 6006
    ports:
      - "6006:6006"

### in .env file:

POSTGRES_USER=phoenix
POSTGRES_PASSWORD=phoenix
POSTGRES_DB=phoenix
PHOENIX_HOST=0.0.0.0
PHOENIX_PORT=6006

### Start the stack:
UI: http://localhost:6006
docker compose up -d
To log views:
docker compose up -d --force-recreate --no-deps phoenix
docker compose logs -f phoenix

To stop:
docker compose down
 docker compose down && docker compose up -d
uv run main.py

### You need to install docker:
Install Docker Desktop (one-time setup): https://docs.docker.com/desktop/setup/install/mac-install/
Download from: Docker Desktop for Mac
Pick the Apple Silicon (M1/M2/M3) version if your MacBook Air is ARM-based.
Open the .dmg file and drag Docker.app into Applications.
Launch Docker.app once → it stays in your menu bar. The first launch may ask for system permissions.

##### Verify installation in terminal:
docker --version
docker compose version




