import os
import logging
from dotenv import load_dotenv
from rich.logging import RichHandler
from rich.console import Console
from util import print_graph_structure, print_detailed_graph_structure, try_generate_visual_graph
from workflow import get_workflow

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

# Environment variables
LLM_API_KEY = os.getenv("LLM_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "100"))

if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY not set in .env file.")


def analyze_image(image_data):
    """
    Main service function for analyzing images using LangGraph workflow.
    
    This function takes image data and processes it through a multi-stage analysis pipeline:
    1. OCR extraction and content type classification
    2. Conditional routing based on content type:
       - MEME content: meme name identification → humor explanation → sentiment analysis
       - ARTICLE/FACTS content: web search → sentiment analysis
       - OTHER content: direct to sentiment analysis
    3. Political content analysis
    4. Outrage content analysis
    5. Result aggregation
    
    Args:
        image_data: Raw image bytes or file path to image
        
    Returns:
        dict: Analysis results containing:
            - text: Extracted OCR text
            - content_type: Classified content type (MEME/ARTICLE/FACTS/OTHER)
            - search_results: Web search results (for ARTICLE/FACTS)
            - meme_name: Identified meme format name (for MEME content)
            - explain_humor: Humor explanation (for MEME content)
            - sentiment: Sentiment analysis (POSITIVE/NEGATIVE/NEUTRAL)
            - is_political: Political content detection (YES/NO)
            - is_outrage: Outrage content detection (YES/NO)
            - usage: Token usage and cost information
    """
    # Get the compiled workflow
    graph = get_workflow(image_data)
    
    # Print graph structure (if enabled)
    print_graph_structure(None, graph)
    
    result = graph.invoke({})
    
    # Debug: Log the final result state
    logger.info(f"Final result state: {result}")
    
    return {
        "text": result.get("ocr_result", ""),
        "content_type": result.get("content_type", ""),
        "search_results": result.get("search_results", ""),
        "meme_name": result.get("meme_name", ""),
        "explain_humor": result.get("explain_humor", ""),
        "sentiment": result.get("sentiment", ""),
        "is_political": result.get("is_political", ""),
        "is_outrage": result.get("is_outrage", ""),
        "usage": result.get("cb", {})
    }

def main():
    """Visualize the LangGraph structure and generate PNG image"""
    logger.info("Building LangGraph workflow for visualization...")
    
    # Get the workflow (with dummy image data for structure)
    graph = get_workflow(None)
    
    # Print detailed graph structure (if enabled)
    print_detailed_graph_structure()
    
    # Try to generate visual graph (if enabled)
    try_generate_visual_graph(graph)

if __name__ == "__main__":
    main()

