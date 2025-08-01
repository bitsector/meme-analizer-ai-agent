import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def print_graph_structure(workflow, graph):
    """Print the LangGraph structure if PRINT_GRAPH is enabled"""
    print_graph = os.getenv("PRINT_GRAPH", "0")
    if print_graph == "0":
        return
    
    logger.info("LangGraph Structure:")
    try:
        # Print nodes
        nodes = list(workflow.nodes.keys())
        logger.info(f"Nodes: {', '.join(nodes)}")
        
        # Print edges - avoiding the 'set' object error
        edges = []
        for source in workflow.edges:
            logger.info(f"Edge from {source}")
        
        # Print entry point
        logger.info(f"Entry Point: ocr")
        
    except Exception as e:
        logger.error(f"Error printing graph structure: {str(e)}")

def print_detailed_graph_structure():
    """Print detailed graph structure for main() function"""
    print_graph = os.getenv("PRINT_GRAPH", "0")
    if print_graph == "0":
        return
    
    logger.info("=== LangGraph Workflow Structure ===")
    
    try:
        # Print nodes with descriptions
        logger.info("NODES:")
        logger.info("  • ocr: Extracts text from image using GPT-4o-mini vision")
        logger.info("  • search: Searches web for ARTICLE/FACTS content using DuckDuckGo")
        logger.info("  • sentiment_analysis: Analyzes sentiment (POSITIVE/NEGATIVE/NEUTRAL)")
        logger.info("  • political_analysis: Detects political content (YES/NO)")
        logger.info("  • outrage_analysis: Detects outrage/inflammatory content (YES/NO)")
        logger.info("  • result: Final result aggregation node")
        
        # Print edges (flow)
        logger.info("WORKFLOW FLOW:")
        logger.info("  START → ocr → conditional")
        logger.info("    ├─ if MEME/OTHER → sentiment_analysis")
        logger.info("    └─ if ARTICLE/FACTS → search → sentiment_analysis")
        logger.info("  sentiment_analysis → political_analysis → outrage_analysis → result → END")
        
        # Print entry point
        logger.info(f"ENTRY POINT: ocr")
        
        # Print state schema
        logger.info("STATE SCHEMA:")
        logger.info("  • ocr_result: str - Extracted text from image")
        logger.info("  • content_type: str - MEME/ARTICLE/FACTS/OTHER")
        logger.info("  • search_results: str - Web search results")
        logger.info("  • sentiment: str - POSITIVE/NEGATIVE/NEUTRAL")
        logger.info("  • is_political: str - YES/NO")
        logger.info("  • is_outrage: str - YES/NO")
        logger.info("  • cb: dict - Token usage and cost info")
        
        logger.info("Graph structure displayed successfully!")
        
    except Exception as e:
        logger.error(f"Error displaying graph structure: {str(e)}")

def try_generate_visual_graph(graph):
    """Try to generate visual graph PNG"""
    print_graph = os.getenv("PRINT_GRAPH", "0")
    if print_graph == "0":
        return
    
    logger.info("GENERATING VISUAL GRAPH...")
    try:
        # LangGraph has built-in visualization
        graph_png = graph.get_graph().draw_mermaid_png()
        
        # Save to file
        with open("langgraph_workflow.png", "wb") as f:
            f.write(graph_png)
        logger.info("Graph saved as 'langgraph_workflow.png'!")
        
    except ImportError as ie:
        logger.warning(f"Visual graph generation requires additional packages: {str(ie)}")
        logger.info("To install: pip install 'langgraph[mermaid]'")
        
    except Exception as ve:
        logger.warning(f"Visual graph generation failed: {str(ve)}")
        logger.info("Showing text representation instead")
        
        # Fallback: ASCII art representation
        logger.info("ASCII GRAPH:")
        logger.info("┌─────────┐")
        logger.info("│  START  │")
        logger.info("└────┬────┘")
        logger.info("     │")
        logger.info("┌────▼────┐")
        logger.info("│   OCR   │ ← GPT-4o-mini Vision")
        logger.info("└────┬────┘")
        logger.info("     │")
        logger.info("   ┌─▼─┐ CONDITIONAL")
        logger.info("   │ ? │")
        logger.info("   └┬─┬┘")
        logger.info("MEME│ │ARTICLE/FACTS")
        logger.info("    │ │")
        logger.info("    │ └──┐")
        logger.info("    │    ▼")
        logger.info("    │ ┌────────┐")
        logger.info("    │ │ SEARCH │ ← DuckDuckGo")
        logger.info("    │ └───┬────┘")
        logger.info("    │     │")
        logger.info("    ▼     ▼")
        logger.info("┌─────────────────┐")
        logger.info("│ SENTIMENT       │ ← GPT-4o-mini")
        logger.info("│ ANALYSIS        │")
        logger.info("└────────┬────────┘")
        logger.info("         │")
        logger.info("┌────────▼────────┐")
        logger.info("│ POLITICAL       │ ← GPT-4o-mini")
        logger.info("│ ANALYSIS        │")
        logger.info("└────────┬────────┘")
        logger.info("         │")
        logger.info("┌────────▼────────┐")
        logger.info("│ OUTRAGE         │ ← GPT-4o-mini")
        logger.info("│ ANALYSIS        │")
        logger.info("└────────┬────────┘")
        logger.info("         │")
        logger.info("┌────────▼────────┐")
        logger.info("│     RESULT      │")
        logger.info("└────┬────────────┘")
        logger.info("     │")
        logger.info("┌────▼────┐")
        logger.info("│   END   │")
        logger.info("└─────────┘")