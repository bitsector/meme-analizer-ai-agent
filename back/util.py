import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from logging_config import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


def get_secret(secret_name: str) -> str:
    """Read secret from file or environment variable"""
    # Try file-based secret first (Docker/Cloud Run volumes)
    secret_file = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_file):
        logger.debug(f"Reading secret {secret_name} from file: {secret_file}")
        return Path(secret_file).read_text().strip()
    
    # Fallback to environment variable (uppercase)
    env_value = os.getenv(secret_name.upper())
    if env_value:
        logger.debug(f"Reading secret {secret_name} from environment variable")
        return env_value
    
    # Try original case for backward compatibility
    env_value = os.getenv(secret_name)
    if env_value:
        logger.debug(f"Reading secret {secret_name} from environment variable (original case)")
        return env_value
    
    raise ValueError(f"Secret {secret_name} not found in file (/run/secrets/{secret_name}) or environment")


class ModelConfig:
    """Configuration class for all LLM models"""
    
    def __init__(self):
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        if self.llm_provider == "openai":
            try:
                self.api_key = get_secret("open_api_key")
            except ValueError:
                # Fallback for backward compatibility
                self.api_key = os.getenv("LLM_API_KEY")
                if not self.api_key:
                    raise ValueError("OpenAI API key not found in secrets or environment variables")
        elif self.llm_provider == "gemini":
            try:
                self.api_key = get_secret("gemini_api_key")
            except ValueError:
                self.api_key = os.getenv("GEMINI_API_KEY")
                if not self.api_key:
                    raise ValueError("Gemini API key not found in secrets or environment variables")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        # Set models based on provider
        if self.llm_provider == "openai":
            self.completion_model = os.getenv("COMPLETION_MODEL", "gpt-4o-mini")
            self.image_gen_model = os.getenv("IMAGE_GEN_MODEL", "dall-e-2")
            self.tts_model = os.getenv("TTS_MODEL", "tts-1")
        elif self.llm_provider == "gemini":
            self.completion_model = os.getenv("COMPLETION_MODEL", "gemini-1.5-flash")
            self.image_gen_model = None  # Gemini doesn't have image generation
            self.tts_model = None  # Gemini doesn't have TTS
        
        self.max_tokens = int(os.getenv("MAX_TOKENS", "100"))
        self.print_graph = os.getenv("PRINT_GRAPH", "0") == "1"
    
    def get_completion_model(self):
        return self.completion_model
    
    def get_image_gen_model(self):
        return self.image_gen_model
    
    def get_tts_model(self):
        return self.tts_model
    
    def get_max_tokens(self):
        return self.max_tokens
    
    def get_api_key(self):
        return self.api_key
    
    def get_llm_provider(self):
        return self.llm_provider
    
    def should_print_graph(self):
        return self.print_graph


# Global model configuration instance
model_config = ModelConfig()


def encode_image_to_base64(image_data):
    """Convert image data to base64 string for OpenAI Vision API"""
    if isinstance(image_data, str):
        with open(image_data, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    else:
        return base64.b64encode(image_data).decode("utf-8")

def print_graph_structure(workflow, graph):
    """Print the LangGraph structure if PRINT_GRAPH is enabled"""
    if not model_config.should_print_graph():
        return
    
    logger.info("LangGraph Structure:")
    try:
        # Just skip the detailed graph printing for now to avoid errors
        logger.info("Graph compiled successfully")
        logger.info("Entry Point: ocr")
        logger.info("Workflow contains: OCR → Conditional Routing → Analysis → Result")
        
    except Exception as e:
        logger.error(f"Error printing graph structure: {str(e)}")

def print_detailed_graph_structure():
    """Print detailed graph structure for main() function"""
    if not model_config.should_print_graph():
        return
    
    logger.info("=== LangGraph Workflow Structure ===")
    
    try:
        # Print nodes with descriptions
        logger.info("NODES:")
        logger.info("  • ocr: Extracts text from image using GPT-4o-mini vision")
        logger.info("  • search: Searches web for ARTICLE/FACTS content using DuckDuckGo")
        logger.info("  • meme_name_analysis: Identifies meme format names for MEME content")
        logger.info("  • explain_humor_analysis: Explains why memes are funny")
        logger.info("  • social_media_detection: Identifies social media platform from UI")
        logger.info("  • recognise_poster: Identifies who posted the social media content")
        logger.info("  • sentiment_analysis: Analyzes sentiment (POSITIVE/NEGATIVE/NEUTRAL)")
        logger.info("  • political_analysis: Detects political content (YES/NO)")
        logger.info("  • outrage_analysis: Detects outrage/inflammatory content (YES/NO)")
        logger.info("  • result: Final result aggregation node")
        
        # Print edges (flow)
        logger.info("WORKFLOW FLOW:")
        logger.info("  START → ocr → conditional")
        logger.info("    ├─ if MEME → meme_name_analysis → explain_humor_analysis → sentiment_analysis")
        logger.info("    ├─ if ARTICLE/FACTS → search → sentiment_analysis")
        logger.info("    ├─ if SOCIAL_MEDIA → social_media_detection → recognise_poster → sentiment_analysis")
        logger.info("    └─ if OTHER → sentiment_analysis")
        logger.info("  sentiment_analysis → political_analysis → outrage_analysis → result → END")
        
        # Print entry point
        logger.info(f"ENTRY POINT: ocr")
        
        # Print state schema
        logger.info("STATE SCHEMA:")
        logger.info("  • ocr_result: str - Extracted text from image")
        logger.info("  • content_type: str - MEME/ARTICLE/FACTS/SOCIAL_MEDIA/OTHER")
        logger.info("  • search_results: str - Web search results")
        logger.info("  • meme_name: str - Identified meme format name")
        logger.info("  • explain_humor: str - Humor analysis explanation")
        logger.info("  • social_media_platform: str - Detected platform (TWITTER/FACEBOOK/etc)")
        logger.info("  • poster_name: str - Username/name of content poster")
        logger.info("  • sentiment: str - POSITIVE/NEGATIVE/NEUTRAL")
        logger.info("  • is_political: str - YES/NO")
        logger.info("  • is_outrage: str - YES/NO")
        logger.info("  • cb: dict - Token usage and cost info")
        
        logger.info("Graph structure displayed successfully!")
        
    except Exception as e:
        logger.error(f"Error displaying graph structure: {str(e)}")

def try_generate_visual_graph(graph):
    """Try to generate visual graph PNG"""
    if not model_config.should_print_graph():
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
        logger.info("                    ┌─────────┐")
        logger.info("                    │  START  │")
        logger.info("                    └────┬────┘")
        logger.info("                         │")
        logger.info("                    ┌────▼────┐")
        logger.info("                    │   OCR   │ ← GPT-4o-mini Vision")
        logger.info("                    └────┬────┘")
        logger.info("                         │")
        logger.info("                    ┌────▼────┐ CONDITIONAL ROUTING")
        logger.info("                    │    ?    │")
        logger.info("           ┌────────┴────┬────┴────────┬────────┐")
        logger.info("           │             │             │        │")
        logger.info("      MEME │        ARTICLE/FACTS  SOCIAL_MEDIA │ OTHER")
        logger.info("           ▼             ▼             ▼        ▼")
        logger.info("    ┌─────────────┐ ┌─────────┐ ┌─────────────┐ │")
        logger.info("    │ MEME NAME   │ │ SEARCH  │ │ SOCIAL      │ │")
        logger.info("    │ ANALYSIS    │ │         │ │ MEDIA       │ │")
        logger.info("    └──────┬──────┘ └────┬────┘ │ DETECTION   │ │")
        logger.info("           │             │      └──────┬──────┘ │")
        logger.info("           ▼             │             ▼        │")
        logger.info("    ┌─────────────┐      │      ┌─────────────┐ │")
        logger.info("    │ EXPLAIN     │      │      │ RECOGNISE   │ │")
        logger.info("    │ HUMOR       │      │      │ POSTER      │ │")
        logger.info("    └──────┬──────┘      │      └──────┬──────┘ │")
        logger.info("           │             │             │        │")
        logger.info("           └─────────────┼─────────────┘        │")
        logger.info("                         ▼                      │")
        logger.info("                  ┌─────────────┐               │")
        logger.info("                  │ SENTIMENT   │ ← GPT-4o-mini │")
        logger.info("                  │ ANALYSIS    │◄──────────────┘")
        logger.info("                  └──────┬──────┘")
        logger.info("                         │")
        logger.info("                  ┌──────▼──────┐")
        logger.info("                  │ POLITICAL   │ ← GPT-4o-mini")
        logger.info("                  │ ANALYSIS    │")
        logger.info("                  └──────┬──────┘")
        logger.info("                         │")
        logger.info("                  ┌──────▼──────┐")
        logger.info("                  │ OUTRAGE     │ ← GPT-4o-mini")
        logger.info("                  │ ANALYSIS    │")
        logger.info("                  └──────┬──────┘")
        logger.info("                         │")
        logger.info("                  ┌──────▼──────┐")
        logger.info("                  │   RESULT    │")
        logger.info("                  └──────┬──────┘")
        logger.info("                         │")
        logger.info("                    ┌────▼────┐")
        logger.info("                    │   END   │")
        logger.info("                    └─────────┘")