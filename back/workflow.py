from typing import TypedDict

from langgraph.graph import END, StateGraph
from logging_config import get_logger
from nodes import (create_explain_humor_analysis_node,
                   create_meme_name_analysis_node, create_ocr_node,
                   create_outrage_analysis_node,
                   create_political_analysis_node,
                   create_recognise_poster_node, create_result_node,
                   create_search_node, create_sentiment_analysis_node,
                   create_social_media_detection_node)


# Define the state schema
class GraphState(TypedDict):
    ocr_result: str
    content_type: str
    search_results: str
    meme_name: str
    explain_humor: str
    social_media_platform: str
    poster_name: str
    sentiment: str
    is_political: str
    is_outrage: str
    cb: dict


def should_search(state):
    """Conditional routing: search for ARTICLE/FACTS, meme analysis for MEME, social media for SOCIAL_MEDIA, sentiment for OTHER"""
    content_type = state.get("content_type", "OTHER")
    if content_type in ["ARTICLE", "FACTS"]:
        return "search"
    elif content_type == "MEME":
        return "meme_name_analysis"
    elif content_type == "SOCIAL_MEDIA":
        return "social_media_detection"
    else:
        return "sentiment_analysis"


def get_workflow(image_data):
    """
    Create and return a compiled LangGraph workflow for image analysis.

    The workflow is built fresh for each analysis request to ensure:
    1. Clean state initialization
    2. Proper image data binding to OCR node
    3. No cross-request state contamination
    4. Consistent behavior across multiple requests

    Args:
        image_data: Raw image bytes or file path to image

    Returns:
        Compiled LangGraph workflow ready for execution
    """
    workflow = StateGraph(GraphState)

    # Add all nodes to the workflow
    workflow.add_node("ocr", create_ocr_node(image_data))
    workflow.add_node("search", create_search_node())
    workflow.add_node("meme_name_analysis", create_meme_name_analysis_node())
    workflow.add_node("explain_humor_analysis", create_explain_humor_analysis_node())
    workflow.add_node("social_media_detection", create_social_media_detection_node())
    workflow.add_node("recognise_poster", create_recognise_poster_node())
    workflow.add_node("sentiment_analysis", create_sentiment_analysis_node())
    workflow.add_node("political_analysis", create_political_analysis_node())
    workflow.add_node("outrage_analysis", create_outrage_analysis_node())
    workflow.add_node("result", create_result_node())

    # Define workflow flow
    workflow.set_entry_point("ocr")
    workflow.add_conditional_edges("ocr", should_search)
    workflow.add_edge("search", "sentiment_analysis")
    workflow.add_edge("meme_name_analysis", "explain_humor_analysis")
    workflow.add_edge("explain_humor_analysis", "sentiment_analysis")
    workflow.add_edge("social_media_detection", "recognise_poster")
    workflow.add_edge("recognise_poster", "sentiment_analysis")
    workflow.add_edge("sentiment_analysis", "political_analysis")
    workflow.add_edge("political_analysis", "outrage_analysis")
    workflow.add_edge("outrage_analysis", "result")
    workflow.add_edge("result", END)

    # Compile and return the workflow
    return workflow.compile()
