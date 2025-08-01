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
    
    logger.info("[bold magenta]LangGraph Structure:[/bold magenta]")
    try:
        # Print nodes
        nodes = list(workflow.nodes.keys())
        logger.info(f"[cyan]Nodes:[/cyan] {', '.join(nodes)}")
        
        # Print edges - avoiding the 'set' object error
        edges = []
        for source in workflow.edges:
            logger.info(f"[cyan]Edge from {source}[/cyan]")
        
        # Print entry point
        logger.info(f"[cyan]Entry Point:[/cyan] ocr")
        
    except Exception as e:
        logger.error(f"[bold red]Error printing graph structure:[/bold red] {str(e)}")

def print_detailed_graph_structure():
    """Print detailed graph structure for main() function"""
    print_graph = os.getenv("PRINT_GRAPH", "0")
    if print_graph == "0":
        return
    
    logger.info("[bold magenta]═══ LangGraph Workflow Structure ═══[/bold magenta]")
    
    try:
        # Print nodes with descriptions
        logger.info("[bold cyan]📍 NODES:[/bold cyan]")
        logger.info("  • [yellow]ocr[/yellow]: Extracts text from image using GPT-4o-mini vision")
        logger.info("  • [yellow]search[/yellow]: Searches web for ARTICLE/FACTS content using DuckDuckGo")
        logger.info("  • [yellow]sentiment_analysis[/yellow]: Analyzes sentiment (POSITIVE/NEGATIVE/NEUTRAL)")
        logger.info("  • [yellow]political_analysis[/yellow]: Detects political content (YES/NO)")
        logger.info("  • [yellow]outrage_analysis[/yellow]: Detects outrage/inflammatory content (YES/NO)")
        logger.info("  • [yellow]result[/yellow]: Final result aggregation node")
        
        # Print edges (flow)
        logger.info("[bold cyan]🔗 WORKFLOW FLOW:[/bold cyan]")
        logger.info("  [green]START[/green] → [yellow]ocr[/yellow] → [magenta]conditional[/magenta]")
        logger.info("    ├─ if MEME/OTHER → [yellow]sentiment_analysis[/yellow]")
        logger.info("    └─ if ARTICLE/FACTS → [yellow]search[/yellow] → [yellow]sentiment_analysis[/yellow]")
        logger.info("  [yellow]sentiment_analysis[/yellow] → [yellow]political_analysis[/yellow] → [yellow]outrage_analysis[/yellow] → [yellow]result[/yellow] → [red]END[/red]")
        
        # Print entry point
        logger.info(f"[bold cyan]🚀 ENTRY POINT:[/bold cyan] [yellow]ocr[/yellow]")
        
        # Print state schema
        logger.info("[bold cyan]📊 STATE SCHEMA:[/bold cyan]")
        logger.info("  • [blue]ocr_result[/blue]: str - Extracted text from image")
        logger.info("  • [blue]content_type[/blue]: str - MEME/ARTICLE/FACTS/OTHER")
        logger.info("  • [blue]search_results[/blue]: str - Web search results")
        logger.info("  • [blue]sentiment[/blue]: str - POSITIVE/NEGATIVE/NEUTRAL")
        logger.info("  • [blue]is_political[/blue]: str - YES/NO")
        logger.info("  • [blue]is_outrage[/blue]: str - YES/NO")
        logger.info("  • [blue]cb[/blue]: dict - Token usage and cost info")
        
        logger.info("[bold green]✅ Graph structure displayed successfully![/bold green]")
        
    except Exception as e:
        logger.error(f"[bold red]❌ Error displaying graph structure:[/bold red] {str(e)}")

def try_generate_visual_graph(graph):
    """Try to generate visual graph PNG"""
    print_graph = os.getenv("PRINT_GRAPH", "0")
    if print_graph == "0":
        return
    
    logger.info("[bold cyan]🎨 GENERATING VISUAL GRAPH...[/bold cyan]")
    try:
        # LangGraph has built-in visualization
        graph_png = graph.get_graph().draw_mermaid_png()
        
        # Save to file
        with open("langgraph_workflow.png", "wb") as f:
            f.write(graph_png)
        logger.info("[bold green]✅ Graph saved as 'langgraph_workflow.png'![/bold green]")
        
    except ImportError as ie:
        logger.warning(f"[bold yellow]⚠️  Visual graph generation requires additional packages:[/bold yellow] {str(ie)}")
        logger.info("[bold yellow]💡 To install: pip install 'langgraph[mermaid]'[/bold yellow]")
        
    except Exception as ve:
        logger.warning(f"[bold yellow]⚠️  Visual graph generation failed:[/bold yellow] {str(ve)}")
        logger.info("[bold yellow]💡 Showing text representation instead[/bold yellow]")
        
        # Fallback: ASCII art representation
        logger.info("[bold cyan]📊 ASCII GRAPH:[/bold cyan]")
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