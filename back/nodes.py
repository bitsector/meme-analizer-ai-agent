from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage
from util import encode_image_to_base64, model_config
from logging_config import get_logger

logger = get_logger(__name__)




def create_ocr_node(image_data):
    """Create OCR node that extracts text and classifies content type"""
    def ocr_node(state):
        image_b64 = encode_image_to_base64(image_data)
        prompt = [
            HumanMessage(content=[
                {"type": "text", "text": """Please analyze this image and provide:

                1. OCR: Extract all the text you see in the image
                2. CONTENT_TYPE: Classify the content as one of these categories:
                   - MEME: Humorous images, jokes, memes (NOT social media screenshots)
                   - ARTICLE: News articles, blog posts, formal written content, journalistic text
                   - FACTS: Educational content, Wikipedia-style information, factual data, statistics
                   - SOCIAL_MEDIA: Screenshots of social media posts (Twitter/X, Facebook, Instagram, Reddit, TikTok, etc.) with visible platform UI elements like usernames, avatars, timestamps, like/share buttons
                   - OTHER: None of the above categories

                Format your response exactly like this:
                OCR: [extracted text here]
                CONTENT_TYPE: [MEME/ARTICLE/FACTS/SOCIAL_MEDIA/OTHER]"""},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ])
        ]
        llm = ChatOpenAI(
            api_key=model_config.get_api_key(),
            model=model_config.get_completion_model(),
            max_tokens=512
        )
        try:
            with get_openai_callback() as cb:
                response = llm.invoke(prompt)
                cb_info = {
                    "prompt_tokens": cb.prompt_tokens,
                    "completion_tokens": cb.completion_tokens,
                    "total_tokens": cb.total_tokens,
                    "total_cost": cb.total_cost,
                }
        except Exception as e:
            error_msg = str(e)
            if "unsupported_country_region_territory" in error_msg or "403" in error_msg:
                logger.error("OpenAI API is not available in your region. Please use a VPN or try Azure OpenAI.")
                return {
                    "ocr_result": "Error: OpenAI API blocked in your region", 
                    "content_type": "ERROR",
                    "search_results": "",
                    "meme_name": "",
                    "explain_humor": "",
                    "social_media_platform": "",
                    "poster_name": "",
                    "sentiment": "",
                    "is_political": "",
                    "is_outrage": "",
                    "cb": {"error": error_msg}
                }
            else:
                raise e
        
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
            "social_media_platform": "",
            "poster_name": "",
            "sentiment": "",
            "is_political": "",
            "is_outrage": "",
            "cb": cb_info
        }
    return ocr_node


def create_search_node():
    """Create search node that performs web search for ARTICLE/FACTS content"""
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
    """Create meme name analysis node for identifying popular meme formats"""
    def meme_name_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        content_type = state.get("content_type", "")
        
        # Only analyze meme names for MEME content
        if content_type != "MEME" or not ocr_result.strip():
            logger.info("Skipping meme name analysis - not a meme or no text")
            return {**state, "meme_name": "N/A"}
        
        logger.info("Analyzing meme name...")
        
        llm = ChatOpenAI(
            api_key=model_config.get_api_key(),
            model=model_config.get_completion_model(),
            max_tokens=model_config.get_max_tokens()
        )
        
        prompt = f"""Identify this meme format by analyzing both the visual structure and text content. 

        VISUAL ANALYSIS (Primary):
        - Examine the image layout, composition, and visual elements
        - Look for recognizable faces, objects, or scenes from popular meme templates
        - Note text positioning (top/bottom, overlay style, speech bubbles, etc.)
        - Consider color schemes, image quality, and visual style

        TEXT ANALYSIS (Secondary):
        - Analyze the text pattern and structure
        - Look for characteristic phrases or text formats
        - Consider how text relates to the visual elements

        COMMON MEME PATTERNS TO CONSIDER:
        - Reaction memes (facial expressions + relatable text)
        - Comparison memes (side-by-side formats like Drake pointing)
        - Narrative memes (multi-panel storytelling)
        - Advice/Impact font memes (bold white text on colored backgrounds)  
        - Modern Twitter/social media screenshot formats
        - Classic image macro formats

        Text from image: {ocr_result}

        IDENTIFICATION PROCESS:
        1. First analyze the visual template/format
        2. Then consider how the text fits the visual pattern
        3. Match against known meme formats

        RESPONSE FORMAT:
        - If you can identify a specific, well-known meme format: respond with the exact meme name
        - If it follows a recognizable pattern but isn't a specific named meme: respond with the pattern type (e.g., "Reaction Meme", "Comparison Meme", "Text Overlay Meme")
        - If it's completely custom or unrecognizable: respond with "Custom Meme"

        Respond with only the meme name or category, nothing else."""
        
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


def create_social_media_detection_node():
    """Create social media platform detection node for identifying the specific platform"""
    def social_media_detection_node(state):
        ocr_result = state.get("ocr_result", "")
        content_type = state.get("content_type", "")
        
        # Only analyze social media platform for SOCIAL_MEDIA content
        if content_type != "SOCIAL_MEDIA" or not ocr_result.strip():
            logger.info("Skipping social media detection - not social media content or no text")
            return {**state, "social_media_platform": "N/A"}
        
        logger.info("Detecting social media platform...")
        
        llm = ChatOpenAI(
            api_key=model_config.get_api_key(),
            model=model_config.get_completion_model(),
            max_tokens=model_config.get_max_tokens()
        )
        
        prompt = f"""Analyze this social media screenshot and identify the specific platform based on visual and textual cues.

        VISUAL INDICATORS TO LOOK FOR:
        - UI Layout: button placement, color schemes, design patterns
        - Typography: font styles, text sizing, formatting
        - Interface Elements: like buttons, share buttons, reply structures
        - Avatar/Profile Image positioning and styling
        - Timestamp formats and positioning
        - Platform-specific icons and symbols

        PLATFORM-SPECIFIC CHARACTERISTICS:
        - TWITTER/X: Blue bird icon, @ mentions, RT/retweet, hashtags, "Replying to", character limits, nested reply structure
        - FACEBOOK: Blue theme, "Like", "Comment", "Share" buttons, reaction emojis, profile pictures on left
        - INSTAGRAM: Square image format, heart icons, @ mentions, # hashtags, "liked by" text, stories indicators
        - REDDIT: Upvote/downvote arrows, "r/" subreddit format, "u/" username format, karma points, nested comments with lines
        - TIKTOK: Vertical video format, @ mentions, # hashtags, like/share/comment icons on right side
        - LINKEDIN: Professional network styling, "connections", job titles, corporate branding
        - DISCORD: Dark theme by default, # channel names, @ mentions, timestamps on right, nested server structure
        - SNAPCHAT: Yellow branding, ghost icons, story indicators
        - YOUTUBE: Play button, subscribe button, view counts, thumbs up/down
        - TELEGRAM: Blue theme, @ usernames, forward arrows, channel indicators

        TEXT CONTENT: {ocr_result}

        ANALYSIS PROCESS:
        1. Examine the visual layout and UI elements visible in the image
        2. Look for platform-specific text patterns (@ mentions, # hashtags, platform terminology)
        3. Check for distinctive visual elements (colors, icons, button styles)
        4. Consider the overall design language and user interface patterns

        RESPONSE: Identify the most likely social media platform. If multiple platforms seem possible, choose the most likely one based on the strongest indicators.

        Respond with only the platform name: TWITTER, FACEBOOK, INSTAGRAM, REDDIT, TIKTOK, LINKEDIN, DISCORD, SNAPCHAT, YOUTUBE, TELEGRAM, or UNKNOWN if unclear."""
        
        try:
            response = llm.invoke(prompt)
            platform = response.content.strip().upper()
            
            # Validate response
            valid_platforms = ["TWITTER", "FACEBOOK", "INSTAGRAM", "REDDIT", "TIKTOK", "LINKEDIN", "DISCORD", "SNAPCHAT", "YOUTUBE", "TELEGRAM", "UNKNOWN"]
            if platform not in valid_platforms:
                platform = "UNKNOWN"
            
            # Handle X/Twitter naming
            if platform == "X":
                platform = "TWITTER"
            
            logger.info(f"Detected platform: {platform}")
            return {**state, "social_media_platform": platform}
            
        except Exception as e:
            logger.error(f"Social media detection failed: {str(e)}")
            return {**state, "social_media_platform": "UNKNOWN"}
    
    return social_media_detection_node


def create_recognise_poster_node():
    """Create poster recognition node for identifying who posted the social media content"""
    def recognise_poster_node(state):
        ocr_result = state.get("ocr_result", "")
        content_type = state.get("content_type", "")
        platform = state.get("social_media_platform", "")
        
        # Only analyze poster for SOCIAL_MEDIA content
        if content_type != "SOCIAL_MEDIA" or not ocr_result.strip():
            logger.info("Skipping poster recognition - not social media content or no text")
            return {**state, "poster_name": "N/A"}
        
        logger.info("Identifying social media poster...")
        
        llm = ChatOpenAI(
            api_key=model_config.get_api_key(),
            model=model_config.get_completion_model(),
            max_tokens=model_config.get_max_tokens()
        )
        
        prompt = f"""Identify the person or account who posted this social media content by analyzing the text and visual elements.

        PLATFORM CONTEXT: {platform}
        
        IDENTIFICATION STRATEGIES:
        
        VISUAL CUES TO EXAMINE:
        - Profile/avatar images: Look for recognizable faces, logos, or profile pictures
        - Username placement: Usually near the top of posts, often bold or prominently displayed
        - Display names vs usernames: Many platforms show both (e.g., "John Smith @johnsmith")
        - Verification badges: Blue checkmarks or other verification indicators
        - Account type indicators: Business accounts, official accounts, etc.

        PLATFORM-SPECIFIC PATTERNS:
        - TWITTER: "@username" format, display name above username, often "Name @handle"
        - FACEBOOK: Full names, sometimes with middle names, profile pictures on left
        - INSTAGRAM: "@username" format, bio information, follower counts
        - REDDIT: "u/username" format, often anonymous or pseudonymous
        - TIKTOK: "@username" format, display names, creator badges
        - LINKEDIN: Professional names, job titles, company affiliations
        - YOUTUBE: Channel names, subscriber counts, creator verification

        TEXT CONTENT: {ocr_result}

        ANALYSIS PROCESS:
        1. Look for the primary poster's name/username (not commenters or people mentioned)
        2. Distinguish between the original poster and any quoted/shared content
        3. Identify if this is a public figure, brand, organization, or private individual
        4. Consider context clues like verification status, follower counts, or professional titles

        IDENTIFICATION CRITERIA:
        - If it's a recognizable public figure (celebrity, politician, journalist, etc.): Provide their real name
        - If it's a brand/organization: Provide the brand/organization name
        - If it's a username/handle: Provide the username
        - If it's unclear or anonymous: Respond with "Anonymous User" or "Unknown User"

        IMPORTANT: Only identify the ORIGINAL POSTER of this content, not people mentioned in comments or replies.

        Respond with only the poster's name or username, nothing else."""
        
        try:
            response = llm.invoke(prompt)
            poster = response.content.strip()
            
            # Clean up response
            if not poster or len(poster) > 100:
                poster = "Unknown User"
            
            # Remove common prefixes if they appear
            poster = poster.replace("@", "").replace("u/", "").strip()
            
            logger.info(f"Identified poster: {poster}")
            return {**state, "poster_name": poster}
            
        except Exception as e:
            logger.error(f"Poster recognition failed: {str(e)}")
            return {**state, "poster_name": "Unknown User"}
    
    return recognise_poster_node


def create_explain_humor_analysis_node():
    """Create humor explanation node for analyzing why memes are funny"""
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
    """Create sentiment analysis node for analyzing emotional tone"""
    def sentiment_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        
        if not ocr_result.strip():
            logger.info("No text to analyze for sentiment")
            return {**state, "sentiment": "NEUTRAL"}
        
        logger.info("Analyzing sentiment...")
        
        llm = ChatOpenAI(
            api_key=model_config.get_api_key(),
            model=model_config.get_completion_model(),
            max_tokens=model_config.get_max_tokens()
        )
        
        prompt = f"""Analyze the sentiment of this text and classify it as one of: POSITIVE, NEGATIVE, NEUTRAL

        Text: {ocr_result}

        Respond with only one word: POSITIVE, NEGATIVE, or NEUTRAL"""
        
        try:
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
    """Create political content analysis node"""
    def political_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        
        if not ocr_result.strip():
            logger.info("No text to analyze for political content")
            return {**state, "is_political": "NO"}
        
        logger.info("Analyzing political content...")
        
        llm = ChatOpenAI(
            api_key=model_config.get_api_key(),
            model=model_config.get_completion_model(),
            max_tokens=model_config.get_max_tokens()
        )
        
        prompt = f"""Analyze if this text contains political content. Political content includes:
        - References to politicians, political parties, elections
        - Policy discussions, government actions
        - Political ideologies, movements
        - Current political events or controversies

        Text: {ocr_result}

        Respond with only: YES or NO"""
        
        try:
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
    """Create outrage content analysis node"""
    def outrage_analysis_node(state):
        ocr_result = state.get("ocr_result", "")
        
        if not ocr_result.strip():
            logger.info("No text to analyze for outrage content")
            return {**state, "is_outrage": "NO"}
        
        logger.info("Analyzing outrage content...")
        
        llm = ChatOpenAI(
            api_key=model_config.get_api_key(),
            model=model_config.get_completion_model(),
            max_tokens=model_config.get_max_tokens()
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
    """Create result aggregation node"""
    def result_node(state):
        return state
    return result_node