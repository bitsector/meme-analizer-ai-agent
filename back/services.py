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
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from util import print_graph_structure, print_detailed_graph_structure, try_generate_visual_graph

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

# Define the state schema
class GraphState(TypedDict):
    ocr_result: str
    content_type: str
    search_results: str
    meme_name: str
    explain_humor: str
    sentiment: str
    is_political: str
    is_outrage: str
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
                {"type": "text", "text": """Please analyze this image and provide:

1. OCR: Extract all the text you see in the image
2. CONTENT_TYPE: Classify the content as one of these categories:
   - MEME: Humorous images, social media posts, jokes, memes
   - ARTICLE: News articles, blog posts, formal written content, journalistic text
   - FACTS: Educational content, Wikipedia-style information, factual data, statistics
   - OTHER: None of the above categories

Format your response exactly like this:
OCR: [extracted text here]
CONTENT_TYPE: [MEME/ARTICLE/FACTS/OTHER]"""},
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
        
        # Parse the response to extract OCR and content type
        response_text = response.content
        ocr_result = ""
        content_type = "OTHER"
        
        try:
            lines = response_text.split('\n')
            for line in lines:
                if line.startswith('OCR:'):
                    ocr_result = line.replace('OCR:', '').strip()
                elif line.startswith('CONTENT_TYPE:'):
                    content_type = line.replace('CONTENT_TYPE:', '').strip()
        except:
            # Fallback: use the entire response as OCR result
            ocr_result = response_text
            content_type = "OTHER"
        
        # Log usage info
        logger.info(f"Usage: {cb.total_tokens} tokens (prompt: {cb.prompt_tokens}, completion: {cb.completion_tokens}), cost: ${cb.total_cost:.6f}")
        
        # Log extracted text and classification
        logger.debug(f"Extracted text:\n{ocr_result}")
        logger.info(f"Content type: {content_type}")
        
        return {
            "ocr_result": ocr_result, 
            "content_type": content_type,
            "search_results": "",
            "meme_name": "",
            "explain_humor": "",
            "sentiment": "",
            "is_political": "",
            "is_outrage": "",
            "cb": cb_info
        }
    return ocr_node

def create_search_node():
    def search_node(state):
        content_type = state.get("content_type", "OTHER")
        ocr_result = state.get("ocr_result", "")
        
        # Only search if content is ARTICLE or FACTS
        if content_type in ["ARTICLE", "FACTS"] and ocr_result.strip():
            try:
                logger.info(f"Searching online for {content_type.lower()} content...")
                
                # Initialize search tool
                search = DuckDuckGoSearchRun()
                
                # Create intelligent search query from OCR text
                # Take first few sentences or key phrases
                search_query = ocr_result[:200].strip()
                if len(search_query) > 100:
                    # Try to cut at sentence boundary
                    sentences = search_query.split('.')
                    if len(sentences) > 1:
                        search_query = sentences[0] + '.'
                
                # Perform search
                search_results = search.run(search_query)
                
                logger.info(f"Found search results")
                logger.debug(f"Search results:\n{search_results}")
                
                return {**state, "search_results": search_results}
                
            except Exception as e:
                logger.error(f"Search failed: {str(e)}")
                return {**state, "search_results": f"Search failed: {str(e)}"}
        else:
            logger.info(f"Skipping search for content type: {content_type}")
            return {**state, "search_results": f"No search performed - {content_type} content doesn't require fact-checking"}
    
    return search_node

def create_meme_name_analysis_node():
    def meme_name_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        content_type = state.get("content_type", "")
        
        # Only analyze meme names for MEME content
        if content_type != "MEME" or not ocr_result.strip():
            logger.info("Skipping meme name analysis - not a meme or no text")
            return {**state, "meme_name": "N/A"}
        
        logger.info("Analyzing meme name...")
        
        llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            model=MODEL,
            max_tokens=MAX_TOKENS
        )
        
        prompt = f"""Identify the name of this meme based on the text content. Look for well-known meme formats like:
        - "Distracted Boyfriend" 
        - "Drake Pointing"
        - "One Does Not Simply"
        - "Hide the Pain Harold"
        - "Good Guy Greg"
        - "Scumbag Steve"
        - "Success Kid"
        - "Grumpy Cat"
        - "This Is Fine"
        - "Expanding Brain"
        - "Woman Yelling at Cat"
        - "Surprised Pikachu"
        - "Roll Safe"
        - "Arthur Fist"
        And many others...

        Text from meme: {ocr_result}

        If you can identify the specific meme format, respond with the meme name. If you cannot identify it or it's a custom/unknown meme, respond with "Unknown Meme" or "Custom Meme".

        Respond with only the meme name, nothing else."""
        
        try:
            response = llm.invoke(prompt)
            meme_name = response.content.strip()
            
            # Clean up response
            if not meme_name or len(meme_name) > 100:
                meme_name = "Unknown Meme"
            
            logger.info(f"Meme name: {meme_name}")
            return {**state, "meme_name": meme_name}
            
        except Exception as e:
            logger.error(f"Meme name analysis failed: {str(e)}")
            return {**state, "meme_name": "Analysis Failed"}
    
    return meme_name_analysis_node

def create_explain_humor_analysis_node():
    def explain_humor_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        content_type = state.get("content_type", "")
        meme_name = state.get("meme_name", "")
        
        # Only explain humor for MEME content
        if content_type != "MEME" or not ocr_result.strip():
            logger.info("Skipping humor explanation - not a meme or no text")
            return {**state, "explain_humor": "N/A"}
        
        logger.info("Explaining meme humor...")
        
        llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            model=MODEL,
            max_tokens=200  # More tokens for detailed explanation
        )
        
        meme_context = f" (Meme format: {meme_name})" if meme_name and meme_name != "Unknown Meme" else ""
        
        prompt = f"""Explain why this meme is funny. Analyze the humor, cultural references, irony, and what makes it amusing{meme_context}.

        Meme text: {ocr_result}

        Consider:
        - What's the joke or punchline?
        - Any cultural references or context needed?
        - Is it relatable humor, absurdist, ironic, or another type?
        - What demographic might find this funny?
        - Any wordplay, visual gags, or timing involved?

        Provide a concise but insightful explanation in 2-3 sentences."""
        
        try:
            response = llm.invoke(prompt)
            explanation = response.content.strip()
            
            # Ensure reasonable length
            if len(explanation) > 500:
                explanation = explanation[:497] + "..."
            elif not explanation:
                explanation = "Humor analysis unavailable"
            
            logger.info(f"Humor explanation generated ({len(explanation)} chars)")
            return {**state, "explain_humor": explanation}
            
        except Exception as e:
            logger.error(f"Humor explanation failed: {str(e)}")
            return {**state, "explain_humor": "Humor analysis failed"}
    
    return explain_humor_analysis_node

def create_sentiment_analysis_node():
    def sentiment_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        
        if not ocr_result.strip():
            logger.info("No text to analyze for sentiment")
            return {**state, "sentiment": "NEUTRAL"}
        
        logger.info("Analyzing sentiment...")
        
        llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            model=MODEL,
            max_tokens=MAX_TOKENS
        )
        
        prompt = f"""Analyze the sentiment of this text and classify it as one of: POSITIVE, NEGATIVE, NEUTRAL

        Text: {ocr_result}

        Respond with only one word: POSITIVE, NEGATIVE, or NEUTRAL"""
        
        try:
            with get_openai_callback() as cb:
                response = llm.invoke(prompt)
                sentiment = response.content.strip().upper()
                
                # Validate response
                if sentiment not in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
                    sentiment = "NEUTRAL"
                
                logger.info(f"Sentiment: {sentiment}")
                return {**state, "sentiment": sentiment}
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {**state, "sentiment": "NEUTRAL"}
    
    return sentiment_analysis_node

def create_political_analysis_node():
    def political_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        
        if not ocr_result.strip():
            logger.info("No text to analyze for political content")
            return {**state, "is_political": "NO"}
        
        logger.info("Analyzing political content...")
        
        llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            model=MODEL,
            max_tokens=MAX_TOKENS
        )
        
        prompt = f"""Analyze if this text contains political content. Political content includes:
        - References to politicians, political parties, elections
        - Policy discussions, government actions
        - Political ideologies, movements
        - Current political events or controversies

        Text: {ocr_result}

        Respond with only: YES or NO"""
        
        try:
            with get_openai_callback() as cb:
                response = llm.invoke(prompt)
                is_political = response.content.strip().upper()
                
                # Validate response
                if is_political not in ["YES", "NO"]:
                    is_political = "NO"
                
                logger.info(f"Political content: {is_political}")
                return {**state, "is_political": is_political}
                
        except Exception as e:
            logger.error(f"Political analysis failed: {str(e)}")
            return {**state, "is_political": "NO"}
    
    return political_analysis_node

def create_outrage_analysis_node():
    def outrage_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        
        if not ocr_result.strip():
            logger.info("No text to analyze for outrage content")
            return {**state, "is_outrage": "NO"}
        
        logger.info("Analyzing outrage content...")
        
        llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            model=MODEL,
            max_tokens=MAX_TOKENS
        )
        
        prompt = f"""Analyze if this text is designed to provoke outrage, anger, or strong emotional reactions. Look for:
        - Inflammatory language, extreme statements
        - Divisive or polarizing content
        - Content designed to make people angry
        - Sensationalized claims or fear-mongering
        - Clickbait-style emotional manipulation

        Text: {ocr_result}

        Respond with only: YES or NO"""
        
        try:
            with get_openai_callback() as cb:
                response = llm.invoke(prompt)
                is_outrage = response.content.strip().upper()
                
                # Validate response
                if is_outrage not in ["YES", "NO"]:
                    is_outrage = "NO"
                
                logger.info(f"Outrage content: {is_outrage}")
                return {**state, "is_outrage": is_outrage}
                
        except Exception as e:
            logger.error(f"Outrage analysis failed: {str(e)}")
            return {**state, "is_outrage": "NO"}
    
    return outrage_analysis_node

def create_result_node():
    def result_node(state):
        return state
    return result_node

def should_search(state):
    """Conditional routing: search only for ARTICLE/FACTS, meme analysis for MEME, sentiment for OTHER"""
    content_type = state.get("content_type", "OTHER")
    if content_type in ["ARTICLE", "FACTS"]:
        return "search"
    elif content_type == "MEME":
        return "meme_name_analysis"
    else:
        return "sentiment_analysis"

def analyze_image(image_data):
    workflow = StateGraph(GraphState)
    workflow.add_node("ocr", create_ocr_node(image_data))
    workflow.add_node("search", create_search_node())
    workflow.add_node("meme_name_analysis", create_meme_name_analysis_node())
    workflow.add_node("explain_humor_analysis", create_explain_humor_analysis_node())
    workflow.add_node("sentiment_analysis", create_sentiment_analysis_node())
    workflow.add_node("political_analysis", create_political_analysis_node())
    workflow.add_node("outrage_analysis", create_outrage_analysis_node())
    workflow.add_node("result", create_result_node())
    
    workflow.set_entry_point("ocr")
    workflow.add_conditional_edges("ocr", should_search)
    workflow.add_edge("search", "sentiment_analysis")
    workflow.add_edge("meme_name_analysis", "explain_humor_analysis")
    workflow.add_edge("explain_humor_analysis", "sentiment_analysis")
    workflow.add_edge("sentiment_analysis", "political_analysis")
    workflow.add_edge("political_analysis", "outrage_analysis")
    workflow.add_edge("outrage_analysis", "result")
    workflow.add_edge("result", END)
    
    graph = workflow.compile()
    
    # Print graph structure (if enabled)
    print_graph_structure(workflow, graph)
    
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
    
    # Create the workflow (same as in analyze_image but without execution)
    workflow = StateGraph(GraphState)
    workflow.add_node("ocr", create_ocr_node(None))  # Dummy node for structure
    workflow.add_node("search", create_search_node())
    workflow.add_node("meme_name_analysis", create_meme_name_analysis_node())
    workflow.add_node("explain_humor_analysis", create_explain_humor_analysis_node())
    workflow.add_node("sentiment_analysis", create_sentiment_analysis_node())
    workflow.add_node("political_analysis", create_political_analysis_node())
    workflow.add_node("outrage_analysis", create_outrage_analysis_node())
    workflow.add_node("result", create_result_node())
    
    workflow.set_entry_point("ocr")
    workflow.add_conditional_edges("ocr", should_search)
    workflow.add_edge("search", "sentiment_analysis")
    workflow.add_edge("meme_name_analysis", "explain_humor_analysis")
    workflow.add_edge("explain_humor_analysis", "sentiment_analysis")
    workflow.add_edge("sentiment_analysis", "political_analysis")
    workflow.add_edge("political_analysis", "outrage_analysis")
    workflow.add_edge("outrage_analysis", "result")
    workflow.add_edge("result", END)
    
    # Compile the graph
    graph = workflow.compile()
    
    # Print detailed graph structure (if enabled)
    print_detailed_graph_structure()
    
    # Try to generate visual graph (if enabled)
    try_generate_visual_graph(graph)

if __name__ == "__main__":
    main()

