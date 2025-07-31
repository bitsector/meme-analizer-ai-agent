import os
import logging
from dotenv import load_dotenv
import base64
from langchain_community.callbacks import get_openai_callback
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict
from rich.logging import RichHandler
from rich.console import Console

# Load environment variables
load_dotenv()

# Setup rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

LLM_API_KEY = os.getenv("LLM_API_KEY")
if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY not set in .env file.")

# Define the state schema
class GraphState(TypedDict):
    ocr_result: str
    cb: dict

def encode_image_to_base64(image_data):
    if isinstance(image_data, str):
        with open(image_data, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    else:
        return base64.b64encode(image_data).decode("utf-8")

def create_ocr_node(image_data):
    def ocr_node(state):
        image_b64 = encode_image_to_base64(image_data)
        from langchain_core.messages import HumanMessage
        prompt = [
            HumanMessage(content=[
                {"type": "text", "text": "Please perform OCR on the following image and return the text you see. Extract all the text you see"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ])
        ]
        llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            model="gpt-4o-mini",
            max_tokens=512
        )
        with get_openai_callback() as cb:
            response = llm.invoke(prompt)
            cb_info = {
                "prompt_tokens": cb.prompt_tokens,
                "completion_tokens": cb.completion_tokens,
                "total_tokens": cb.total_tokens,
                "total_cost": cb.total_cost,
            }
        
        # Log usage info
        logger.info(f"[bold green]Usage:[/bold green] {cb.total_tokens} tokens (prompt: {cb.prompt_tokens}, completion: {cb.completion_tokens}), cost: ${cb.total_cost:.6f}")
        
        # Log extracted text in debug mode
        logger.debug(f"[bold blue]Extracted text:[/bold blue]\n{response.content}")
        
        return {"ocr_result": response.content, "cb": cb_info}
    return ocr_node

def create_result_node():
    def result_node(state):
        return state
    return result_node

def analyze_image(image_data):
    workflow = StateGraph(GraphState)
    workflow.add_node("ocr", create_ocr_node(image_data))
    workflow.add_node("result", create_result_node())
    workflow.set_entry_point("ocr")
    workflow.add_edge("ocr", "result")
    workflow.add_edge("result", END)
    
    graph = workflow.compile()
    result = graph.invoke({})
    
    return {
        "text": result["ocr_result"],
        "usage": result["cb"]
    }

