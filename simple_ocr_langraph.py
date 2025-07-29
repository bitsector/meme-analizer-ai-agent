import os
from dotenv import load_dotenv
from PIL import Image
import base64
from langchain_community.callbacks import get_openai_callback
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict

# Load environment variables
load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY not set in .env file.")

# Define the state schema
class GraphState(TypedDict):
    ocr_result: str
    cb: dict

# Path to the image file (replace with your actual image file name)
IMAGE_PATH = "sample_files/brand_nutella.webp"

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def ocr_node(state):
    # Read and encode the image
    image_b64 = encode_image_to_base64(IMAGE_PATH)
    # Prepare the prompt for the LLM (OpenAI Vision model)
    from langchain_core.messages import HumanMessage
    prompt = [
        HumanMessage(content=[
            {"type": "text", "text": "Please perform OCR on the following image and return the text you see. Extract all the text you see"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
        ])
    ]
    llm = ChatOpenAI(
        api_key=LLM_API_KEY,
        model="gpt-4o-mini",  # switched to mini for cost reduction
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
    return {"ocr_result": response.content, "cb": cb_info}

def print_node(state):
    print("LLM OCR Response:", state["ocr_result"])
    cb = state.get("cb")
    if cb:
        print(f"Prompt tokens: {cb['prompt_tokens']}")
        print(f"Completion tokens: {cb['completion_tokens']}")
        print(f"Total tokens: {cb['total_tokens']}")
        print(f"Cost (USD): {cb['total_cost']}")
    return state

# Build the LangGraph
workflow = StateGraph(GraphState)
workflow.add_node("ocr", ocr_node)
workflow.add_node("print", print_node)
workflow.set_entry_point("ocr")
workflow.add_edge("ocr", "print")
workflow.add_edge("print", END)

graph = workflow.compile()

if __name__ == "__main__":
    # Run the graph
    graph.invoke({})
