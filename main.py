from dotenv import load_dotenv
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# put near your imports
try:
    from langchain_core.messages import AIMessage
except ImportError:
    # fallback for older LangChain versions
    from langchain.schema import AIMessage

def stamp_node(reply: AIMessage, node_name: str) -> AIMessage:
    return AIMessage(
        content=reply.content,
        additional_kwargs={**getattr(reply, "additional_kwargs", {}), "node": node_name},
        response_metadata=getattr(reply, "response_metadata", None),
        usage_metadata=getattr(reply, "usage_metadata", None),
        id=getattr(reply, "id", None),
    )

import os
from dotenv import load_dotenv
from phoenix.otel import register

load_dotenv()
from phoenix.otel import register
import os
print({k: v for k, v in os.environ.items()
       if k.startswith("OTEL_EXPORTER_OTLP") or k == "OTEL_TRACES_EXPORTER"})

register(
    project_name="langgraph-tutorial",
    auto_instrument=True,
    protocol="http/protobuf",
)

# register(project_name="langgraph-tutorial", auto_instrument=True)


""" LangGraph Tutorial: https://www.youtube.com/watch?v=1w5cCXlh7JQ&t=516s
https://langchain-ai.github.io/langgraph/concepts/why-langgraph/
"""


llm = init_chat_model(
    # "anthropic:claude-3-5-sonnet-latest"
    "llama3.2:3b",
    model_provider="ollama",
)
# llm = init_chat_model("ollama/llama3.2:3b")

"""
Implementing a very simple Graph with a single Node:
    START
      |
    chatbot
      |
     END
"""
class State(TypedDict): #Defining the type of information that we want to have as we run through this graph
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

def chatbot(state: State):
    return {"messages": llm.invoke(state["messages"])}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

user_input = input("Enter a message: ")
state = graph.invoke({"messages": [{"role": "user", "content": user_input}]})
print(state["messages"]) #prints all of the messages, number of tokens, the model we used, etc.
print(state["messages"][-1].content)

""" Visualizing your Graph: This code should be running in a Jupyter Notebook Cell 

from IPython.display import Image, display
try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass

"""


"""
Implementing a more complex Graph with multiple Nodes: (We can go between multiple AI agents)
    START
      |
    Classifier(logical/emotional)
      |
    Router(if classification is logical, ask the logical agent to give us a reply and vice versa)
     /   \
logical  therapist
     \   /
      END  
      
In this example, sometimes you want an emotional response and sometimes a very logical response.
Based on what User is saying we can kinda adapt how we respond to them using different AI agents.
"""

# Structured Output Parser - Structured Output Format
class MessageClassifier(BaseModel): # It's going to inherit from BaseModel of Pydantic (Pydantic is a typing system in python)
    message_type: Literal["emotional", "logical"] = Field( ..., description="Classify if the message requires an emotional or logical response.")
    # Literal means it has to have the exact values.

class State(TypedDict):
    messages: Annotated[list, add_messages] #keep track of all messages
    message_type: str | None # emotional/logical message type


#Defining various functions: Nodes or Agents
def classify_message(state: State):
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier) # We are creating a version of our llm that will give us only output that matches this pydantic model
    result = classifier_llm.invoke([
        {
            "role": "system",
            "content": """Classify the user message as either:
            - 'emotional': if it asks for emotional support, therapy, deals with feelings, or personal problems
            - 'logical': if it asks for facts, information, logical analysis, or practical solutions
            """
        },
        { "role": "user", "content": last_message.content}
    ])
    return {"message_type": result.message_type}

def router(state: State):
    message_type = state.get("message_type", "logical") # Set default to logical
    if message_type == "emotional":
        return {"next": "therapist"}
    else:
        return {"next": "logical"}

def therapist_message(state: State):
    last_message = state["messages"][-1]
    messages = [
        {
            "role": "system",
            "content": """ You are a compassionate therapist. Focus on the emotional aspects of the user's message.
            Show empathy, validate their feelings, and help them process their emotions.
            Ask thoughtful questions to help them explore their feelings more deeply.
            Avoid giving logical solutions unless explicitly asked.
            """
        },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages)
    # return {"messages": [{"role": "assistant", "content": reply.content}]}
    # keep the full AIMessage (with metadata)
    # return {"messages": [reply]}
    return {"messages": [stamp_node(reply, "therapist")]}
def logical_message(state: State):
    last_message = state["messages"][-1]
    messages = [
        {
            "role": "system",
            "content": """You are a purely logical assistant. Focus only on facts and information.
            Provide clear, concise answers based on logic and evidence.
            Do not address emotions or provide emotional support.
            Be direct and straightforward in your responses.
            """
        },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages)
    # return {"messages": [{"role": "assistant", "content": reply.content}]}
    # return {"messages": [reply]}
    return {"messages": [stamp_node(reply, "logical")]}


graph_builder = StateGraph(State)
graph_builder.add_node("classifier", classify_message)
graph_builder.add_node("router", router)
graph_builder.add_node("therapist", therapist_message)
graph_builder.add_node("logical", logical_message)

graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")
graph_builder.add_conditional_edges(
    "router",
    lambda state: state.get("next"), # A function that decides which node to go next
    {"therapist": "therapist", "logical": "logical"}
)
graph_builder.add_edge("logical", END)
graph_builder.add_edge("therapist", END)
graph = graph_builder.compile()



def run_chatbot():
    state = {"messages": [], "message_type": None}
    while True:
        user_input = input("Enter a message: ")
        if user_input == "exit":
            print("Goodbye")
            break
        state['messages'] = state.get('messages', []) + [
            {"role": "user", "content": user_input}
        ]
        state = graph.invoke(state)
        if state.get("messages") and len(state["messages"]) > 0:
            last_message = state["messages"][-1]
            print(f"Assistant: {last_message.content}")

            # metadata (depends on provider; Ollama typically fills these)
            usage = getattr(last_message, "usage_metadata", None) or {}
            meta = getattr(last_message, "response_metadata", None) or {}
            node = (getattr(last_message, "additional_kwargs", {}) or {}).get("node")

            if usage or meta or node:
                print({
                    "node": node,  # <-- here it is
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "total_duration_ns": meta.get("total_duration"),
                    "eval_count": meta.get("eval_count"),
                    "prompt_eval_count": meta.get("prompt_eval_count"),
                    "model": meta.get("model_name") or meta.get("model"),
                })

if __name__ == "__main__":
    run_chatbot()
