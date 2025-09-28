"""
LLM API interface for making calls to various language models.

This module provides a unified interface for making API calls to different LLM providers
(OpenAI, Anthropic, Groq, xAI, etc.) using LiteLLM. It includes support for:
- Streaming responses
- Tool calls and function calling
- Retry logic with exponential backoff
- Model-specific configurations
- Comprehensive error handling and logging
"""

from typing import Union, Dict, Any, Optional, AsyncGenerator, List
import os
import asyncio
import time
from datetime import datetime, timedelta
import litellm
from litellm.router import Router
from litellm.files.main import ModelResponse
from litellm.exceptions import (
    Timeout as LiteLLMTimeout,
    RateLimitError as LiteLLMRateLimit,
    AuthenticationError as LiteLLMAuth,
    ServiceUnavailableError as LiteLLMServiceUnavailable,
    APIError as LiteLLMAPIError
)
from core.utils.logger import logger
from core.utils.config import config

# litellm.set_verbose=True
# Let LiteLLM auto-adjust params and drop unsupported ones (e.g., GPT-5 temperature!=1)
litellm.modify_params = True
litellm.drop_params = True

# Constants
MAX_RETRIES = 3
PRIMARY_MODEL_RETRIES = 2  # Additional retries for primary model before fallback
REQUEST_TIMEOUT = 60  # Request timeout in seconds
CIRCUIT_BREAKER_THRESHOLD = 5  # Number of failures before circuit opens
CIRCUIT_BREAKER_TIMEOUT = 300  # Circuit breaker timeout in seconds
HEALTH_CHECK_INTERVAL = 60  # Health check interval in seconds

# Circuit breaker state tracking
circuit_breaker_state = {}
model_health_status = {}
last_health_check = {}

provider_router = None


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass

class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    pass

class LLMQuotaExceededError(LLMError):
    """Raised when LLM quota is exceeded."""
    pass

class LLMAuthenticationError(LLMError):
    """Raised when LLM authentication fails."""
    pass

class LLMServiceUnavailableError(LLMError):
    """Raised when LLM service is unavailable."""
    pass

class LLMRetryError(LLMError):
    """Raised when all retry attempts are exhausted."""
    pass

def setup_api_keys() -> None:
    """Set up API keys from environment variables."""
    providers = [
        "OPENAI",
        "ANTHROPIC",
        "GROQ",
        "OPENROUTER",
        "XAI",
        "MORPH",
        "GEMINI",
        "OPENAI_COMPATIBLE",
    ]
    for provider in providers:
        key = getattr(config, f"{provider}_API_KEY")
        if key:
            logger.debug(f"API key set for provider: {provider}")
        else:
            logger.warning(f"No API key found for provider: {provider}")

    # Set up OpenRouter API base if not already set
    if config.OPENROUTER_API_KEY and config.OPENROUTER_API_BASE:
        os.environ["OPENROUTER_API_BASE"] = config.OPENROUTER_API_BASE
        logger.debug(f"Set OPENROUTER_API_BASE to {config.OPENROUTER_API_BASE}")


    # Set up AWS Bedrock credentials
    aws_access_key = config.AWS_ACCESS_KEY_ID
    aws_secret_key = config.AWS_SECRET_ACCESS_KEY
    aws_region = config.AWS_REGION_NAME

    if aws_access_key and aws_secret_key and aws_region:
        logger.debug(f"AWS credentials set for Bedrock in region: {aws_region}")
        # Configure LiteLLM to use AWS credentials
        os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_key
        os.environ["AWS_REGION_NAME"] = aws_region
    else:
        logger.warning(f"Missing AWS credentials for Bedrock integration - access_key: {bool(aws_access_key)}, secret_key: {bool(aws_secret_key)}, region: {aws_region}")


def setup_provider_router(openai_compatible_api_key: str = None, openai_compatible_api_base: str = None):
    global provider_router
    # Configure primary model with fallbacks
    model_list = [
        {
            "model_name": "gemini/gemini-2.5-flash",
            "litellm_params": {
                "model": "gemini/gemini-2.5-flash",
            },
            "fallbacks": [
                "openai/gpt-5-mini",
                "openai/gpt-5", 
                "gemini/gemini-2.5-flash"
            ]
        },
        {
            "model_name": "openai/gpt-5-mini",
            "litellm_params": {
                "model": "openai/gpt-5-mini",
            },
        },
        {
            "model_name": "openai/gpt-5",
            "litellm_params": {
                "model": "openai/gpt-5",
            },
        },
    ]
    provider_router = Router(model_list=model_list)


def get_openrouter_fallback(model_name: str) -> Optional[str]:
    """Return fallback model based on primary model."""
    if model_name == "gemini/gemini-2.5-flash":
        return "openai/gpt-5-mini"
    elif model_name == "openai/gpt-5-mini":
        return "openai/gpt-5"
    elif model_name == "openai/gpt-5":
        return "gemini/gemini-2.5-flash"
    return None

def _configure_token_limits(params: Dict[str, Any], model_name: str, max_tokens: Optional[int]) -> None:
    """Configure token limits based on model type."""
    if max_tokens is None:
        return
    
    if model_name.startswith("bedrock/") and "claude-3-7" in model_name:
        # For Claude 3.7 in Bedrock, do not set max_tokens or max_tokens_to_sample
        # as it causes errors with inference profiles
        logger.debug(f"Skipping max_tokens for Claude 3.7 model: {model_name}")
        return
    
    is_openai_o_series = 'o1' in model_name
    is_openai_gpt5 = 'gpt-5' in model_name
    param_name = "max_completion_tokens" if (is_openai_o_series or is_openai_gpt5) else "max_tokens"
    params[param_name] = max_tokens

def _configure_anthropic(params: Dict[str, Any], model_name: str, messages: List[Dict[str, Any]]) -> None:
    """Configure Anthropic-specific parameters."""
    if not ("claude" in model_name.lower() or "anthropic" in model_name.lower()):
        return
    
    # Include both prompt caching and extended output beta features
    params["extra_headers"] = {
        "anthropic-beta": "prompt-caching-2024-07-31,max-tokens-3-5-sonnet-2024-07-15"
    }
    logger.debug(f"Added Anthropic-specific headers for prompt caching and extended output")

def _configure_openrouter(params: Dict[str, Any], model_name: str) -> None:
    """Configure OpenRouter-specific parameters."""
    if not model_name.startswith("openrouter/"):
        return
    
    logger.debug(f"Preparing OpenRouter parameters for model: {model_name}")

    # Add optional site URL and app name from config
    site_url = config.OR_SITE_URL
    app_name = config.OR_APP_NAME
    if site_url or app_name:
        extra_headers = params.get("extra_headers", {})
        if site_url:
            extra_headers["HTTP-Referer"] = site_url
        if app_name:
            extra_headers["X-Title"] = app_name
        params["extra_headers"] = extra_headers
        logger.debug(f"Added OpenRouter site URL and app name to headers")

def _configure_bedrock(params: Dict[str, Any], model_name: str, model_id: Optional[str]) -> None:
    """Configure Bedrock-specific parameters."""
    if not model_name.startswith("bedrock/"):
        return
    
    logger.debug(f"Preparing AWS Bedrock parameters for model: {model_name}")

    # Auto-set model_id for Claude 3.7 Sonnet if not provided
    if not model_id and "anthropic.claude-3-7-sonnet" in model_name:
        params["model_id"] = "arn:aws:bedrock:us-west-2:935064898258:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        logger.debug(f"Auto-set model_id for Claude 3.7 Sonnet: {params['model_id']}")

def _configure_openai_gpt5(params: Dict[str, Any], model_name: str) -> None:
    """Configure OpenAI GPT-5 specific parameters."""
    if "gpt-5" not in model_name:
        return
    

    # Drop unsupported temperature param (only default 1 allowed)
    if "temperature" in params and params["temperature"] != 1:
        params.pop("temperature", None)

    # Request priority service tier when calling OpenAI directly

    # Pass via both top-level and extra_body for LiteLLM compatibility
    if not model_name.startswith("openrouter/"):
        params["service_tier"] = "priority"
        extra_body = params.get("extra_body", {})
        if "service_tier" not in extra_body:
            extra_body["service_tier"] = "priority"
        params["extra_body"] = extra_body

def _configure_kimi_k2(params: Dict[str, Any], model_name: str) -> None:
    """Configure Gemini 2.5 Flash-specific parameters."""
    is_kimi_k2 = "kimi-k2" in model_name.lower() or model_name.startswith("moonshotai/kimi-k2")
    if not is_kimi_k2:
        return
    
    params["provider"] = {
        "order": ["groq", "moonshotai"] #, "groq", "together/fp8", "novita/fp8", "baseten/fp8", 
    }

def _configure_thinking(params: Dict[str, Any], model_name: str, enable_thinking: Optional[bool], reasoning_effort: Optional[str]) -> None:
    """Configure reasoning/thinking parameters for supported models."""
    if not enable_thinking:
        return
    

    effort_level = reasoning_effort or 'low'
    is_anthropic = "anthropic" in model_name.lower() or "claude" in model_name.lower()
    is_xai = "xai" in model_name.lower() or model_name.startswith("xai/")
    
    if is_anthropic:
        params["reasoning_effort"] = effort_level
        params["temperature"] = 1.0  # Required by Anthropic when reasoning_effort is used
        logger.info(f"Anthropic thinking enabled with reasoning_effort='{effort_level}'")
    elif is_xai:
        params["reasoning_effort"] = effort_level
        logger.info(f"xAI thinking enabled with reasoning_effort='{effort_level}'")

def _add_fallback_model(params: Dict[str, Any], model_name: str, messages: List[Dict[str, Any]]) -> None:
    """Add fallback models to parameters for retry logic."""
    fallback_models = get_openrouter_fallback(model_name)
    if fallback_models:
        params["fallbacks"] = [fallback_models]
        logger.debug(f"Added fallback model {fallback_models} for {model_name}")

def _classify_error(error: Exception) -> LLMError:
    """Classify LiteLLM errors into specific error types."""
    error_str = str(error).lower()
    
    if isinstance(error, LiteLLMTimeout) or "timeout" in error_str:
        return LLMTimeoutError(f"Request timeout: {error}")
    elif isinstance(error, LiteLLMRateLimit) or "rate limit" in error_str:
        return LLMRateLimitError(f"Rate limit exceeded: {error}")
    elif isinstance(error, LiteLLMAuth) or "authentication" in error_str or "unauthorized" in error_str:
        return LLMAuthenticationError(f"Authentication failed: {error}")
    elif isinstance(error, LiteLLMServiceUnavailable) or "service unavailable" in error_str:
        return LLMServiceUnavailableError(f"Service unavailable: {error}")
    elif "quota" in error_str or "billing" in error_str:
        return LLMQuotaExceededError(f"Quota exceeded: {error}")
    else:
        return LLMError(f"LLM API error: {error}")

def _is_circuit_breaker_open(model_name: str) -> bool:
    """Check if circuit breaker is open for a model."""
    if model_name not in circuit_breaker_state:
        return False
    
    state = circuit_breaker_state[model_name]
    if state["status"] == "open":
        # Check if timeout has passed
        if time.time() - state["last_failure"] > CIRCUIT_BREAKER_TIMEOUT:
            # Reset circuit breaker
            circuit_breaker_state[model_name] = {
                "status": "closed",
                "failure_count": 0,
                "last_failure": 0
            }
            logger.info(f"🔄 Circuit breaker reset for {model_name}")
            return False
        return True
    return False

def _record_failure(model_name: str):
    """Record a failure for circuit breaker."""
    if model_name not in circuit_breaker_state:
        circuit_breaker_state[model_name] = {
            "status": "closed",
            "failure_count": 0,
            "last_failure": 0
        }
    
    state = circuit_breaker_state[model_name]
    state["failure_count"] += 1
    state["last_failure"] = time.time()
    
    if state["failure_count"] >= CIRCUIT_BREAKER_THRESHOLD:
        state["status"] = "open"
        logger.warning(f"🚨 Circuit breaker opened for {model_name} after {state['failure_count']} failures")

def _record_success(model_name: str):
    """Record a success for circuit breaker."""
    if model_name in circuit_breaker_state:
        circuit_breaker_state[model_name] = {
            "status": "closed",
            "failure_count": 0,
            "last_failure": 0
        }

async def _health_check_model(model_name: str) -> bool:
    """Perform a health check on a model."""
    try:
        # Simple health check with minimal request
        test_messages = [{"role": "user", "content": "Hello"}]
        test_params = {
            "model": model_name,
            "messages": test_messages,
            "max_tokens": 1,
            "temperature": 0,
            "timeout": 10  # Short timeout for health check
        }
        
        response = await provider_router.acompletion(**test_params)
        model_health_status[model_name] = "healthy"
        last_health_check[model_name] = time.time()
        return True
    except Exception as e:
        logger.warning(f"Health check failed for {model_name}: {e}")
        model_health_status[model_name] = "unhealthy"
        last_health_check[model_name] = time.time()
        return False

def _should_skip_model(model_name: str) -> bool:
    """Check if model should be skipped due to health or circuit breaker."""
    # Check circuit breaker
    if _is_circuit_breaker_open(model_name):
        return True
    
    # Check health status
    if model_name in model_health_status:
        if model_health_status[model_name] == "unhealthy":
            # Check if enough time has passed to retry health check
            if model_name in last_health_check:
                if time.time() - last_health_check[model_name] > HEALTH_CHECK_INTERVAL:
                    return False  # Allow retry
            return True
    
    return False

def _add_tools_config(params: Dict[str, Any], tools: Optional[List[Dict[str, Any]]], tool_choice: str) -> None:
    """Add tools configuration to parameters."""
    if tools is None:
        return
    
    params.update({
        "tools": tools,
        "tool_choice": tool_choice
    })
    logger.debug(f"Added {len(tools)} tools to API parameters")

def prepare_params(
    messages: List[Dict[str, Any]],
    model_name: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    response_format: Optional[Any] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = "low",
) -> Dict[str, Any]:
    from core.ai_models import model_manager
    resolved_model_name = model_manager.resolve_model_id(model_name)
    logger.debug(f"Model resolution: '{model_name}' -> '{resolved_model_name}'")
    
    params = {
        "model": resolved_model_name,
        "messages": messages,
        "temperature": temperature,
        "response_format": response_format,
        "top_p": top_p,
        "stream": stream,
        "num_retries": MAX_RETRIES + PRIMARY_MODEL_RETRIES,  # Total retries including primary model retries
    }

    if api_key:
        params["api_key"] = api_key
    if api_base:
        params["api_base"] = api_base
    if model_id:
        params["model_id"] = model_id

    if model_name.startswith("openai-compatible/"):
        # Check if have required config either from parameters or environment
        if (not api_key and not config.OPENAI_COMPATIBLE_API_KEY) or (
            not api_base and not config.OPENAI_COMPATIBLE_API_BASE
        ):
            raise LLMError(
                "OPENAI_COMPATIBLE_API_KEY and OPENAI_COMPATIBLE_API_BASE is required for openai-compatible models. If just updated the environment variables,  wait a few minutes or restart the service to ensure they are loaded."
            )
        
        setup_provider_router(api_key, api_base)

    # Handle token limits
    _configure_token_limits(params, resolved_model_name, max_tokens)
    # Add tools if provided
    _add_tools_config(params, tools, tool_choice)
    # Add Anthropic-specific parameters
    _configure_anthropic(params, resolved_model_name, params["messages"])
    # Add OpenRouter-specific parameters
    _configure_openrouter(params, resolved_model_name)
    # Add Bedrock-specific parameters
    _configure_bedrock(params, resolved_model_name, model_id)
    
    _add_fallback_model(params, resolved_model_name, messages)
    # Add OpenAI GPT-5 specific parameters
    _configure_openai_gpt5(params, resolved_model_name)
    # Add Kimi K2-specific parameters
    _configure_kimi_k2(params, resolved_model_name)
    _configure_thinking(params, resolved_model_name, enable_thinking, reasoning_effort)

    return params

async def make_llm_api_call_with_fallback(
    messages: List[Dict[str, Any]],
    model_name: str,
    response_format: Optional[Any] = None,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = "low",
) -> Union[Dict[str, Any], AsyncGenerator, ModelResponse]:
    """
    Make an LLM API call with comprehensive fallback and error handling.
    
    This function implements a robust fallback chain:
    1. Primary model (Gemini 2.5 Flash) with retries
    2. Fallback to GPT-5 Mini
    3. Fallback to GPT-5
    4. Final fallback to Gemini 2.5 Flash
    
    Includes circuit breaker, health checks, and graceful degradation.
    """
    from core.ai_models import model_manager
    resolved_model_name = model_manager.resolve_model_id(model_name)
    
    # Define fallback chain
    fallback_chain = [
        resolved_model_name,
        "openai/gpt-5-mini",
        "openai/gpt-5",
        "gemini/gemini-2.5-flash"
    ]
    
    last_error = None
    
    for i, current_model in enumerate(fallback_chain):
        try:
            logger.info(f"🔄 Attempting model {i+1}/{len(fallback_chain)}: {current_model}")
            
            # Skip if model is unhealthy or circuit breaker is open
            if _should_skip_model(current_model):
                logger.warning(f"⚠️ Skipping {current_model} due to health/circuit breaker status")
                continue
            
            # Make the API call
            response = await make_llm_api_call(
                messages=messages,
                model_name=current_model,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice=tool_choice,
                api_key=api_key,
                api_base=api_base,
                stream=stream,
                top_p=top_p,
                model_id=model_id,
                enable_thinking=enable_thinking,
                reasoning_effort=reasoning_effort,
            )
            
            # Success - record and return
            _record_success(current_model)
            logger.info(f"✅ Successfully completed request with {current_model}")
            return response
            
        except (LLMTimeoutError, LLMRateLimitError, LLMServiceUnavailableError) as e:
            # These errors should trigger fallback
            last_error = e
            logger.warning(f"⚠️ {current_model} failed with {type(e).__name__}: {e}")
            continue
            
        except (LLMAuthenticationError, LLMQuotaExceededError) as e:
            # These errors should not trigger fallback (likely account issues)
            logger.error(f"🚨 Critical error with {current_model}: {e}")
            raise e
            
        except Exception as e:
            # Unexpected errors
            last_error = e
            logger.error(f"❌ Unexpected error with {current_model}: {e}")
            continue
    
    # All models failed
    if last_error:
        raise LLMRetryError(f"All models in fallback chain failed. Last error: {last_error}")
    else:
        raise LLMRetryError("All models in fallback chain failed with no specific error")

async def make_llm_api_call(
    messages: List[Dict[str, Any]],
    model_name: str,
    response_format: Optional[Any] = None,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = "low",
) -> Union[Dict[str, Any], AsyncGenerator, ModelResponse]:
    """
    Make an API call to a language model using LiteLLM.

    Args:
        messages: List of message dictionaries for the conversation
        model_name: Name of the model to use (e.g., "gpt-4", "claude-3", "openrouter/openai/gpt-4", "bedrock/anthropic.claude-3-sonnet-20240229-v1:0")
        response_format: Desired format for the response
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in the response
        tools: List of tool definitions for function calling
        tool_choice: How to select tools ("auto" or "none")
        api_key: Override default API key
        api_base: Override default API base URL
        stream: Whether to stream the response
        top_p: Top-p sampling parameter
        model_id: Optional ARN for Bedrock inference profiles
        enable_thinking: Whether to enable thinking
        reasoning_effort: Level of reasoning effort

    Returns:
        Union[Dict[str, Any], AsyncGenerator]: API response or stream

    Raises:
        LLMRetryError: If API call fails after retries
        LLMError: For other API-related errors
    """
    from core.ai_models import model_manager
    resolved_model_name = model_manager.resolve_model_id(model_name)
    
    # debug <timestamp>.json messages
    logger.debug(f"Making LLM API call to model: {model_name} (Thinking: {enable_thinking}, Effort: {reasoning_effort})")
    logger.info(f"📡 API Call: Using primary model {model_name} with fallback chain: GPT-5 Mini → GPT-5 → Gemini 2.5 Flash")

    logger.info(f"📥 Received {len(messages)} messages for LLM call")
    for i, msg in enumerate(messages):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if isinstance(content, list) and content:
            has_cache = 'cache_control' in content[0] if isinstance(content[0], dict) else False
            content_len = len(str(content[0].get('text', ''))) if isinstance(content[0], dict) else 0
            logger.info(f"  Input msg {i}: role={role}, has_cache={has_cache}, length={content_len}")
    
    params = prepare_params(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        tools=tools,
        tool_choice=tool_choice,
        api_key=api_key,
        api_base=api_base,
        stream=stream,
        top_p=top_p,
        model_id=model_id,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort,
    )
    # Debug: Log what we're sending to LiteLLM
    if 'messages' in params:
        logger.info(f"📨 Sending to LiteLLM: {len(params['messages'])} messages")
        for i, msg in enumerate(params['messages'][:3]):  # Only log first 3 to avoid spam
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if isinstance(content, list) and content:
                has_cache = 'cache_control' in content[0] if isinstance(content[0], dict) else False
                logger.info(f"  Final msg {i}: role={role}, has_cache={has_cache}")
                # Log the actual cache_control value if present
                if has_cache:
                    logger.info(f"    cache_control value: {content[0].get('cache_control')}")
    
    # Log the headers being sent
    if 'extra_headers' in params:
        logger.info(f"📮 Headers to LiteLLM: {params['extra_headers']}")
    
    # Check if model should be skipped
    if _should_skip_model(resolved_model_name):
        logger.warning(f"⚠️ Skipping {resolved_model_name} due to circuit breaker or health status")
        # Try fallback immediately
        fallback_model = get_openrouter_fallback(resolved_model_name)
        if fallback_model:
            logger.info(f"🔄 Attempting immediate fallback to {fallback_model}")
            params["model"] = fallback_model
        else:
            raise LLMServiceUnavailableError(f"Model {resolved_model_name} is unavailable and no fallback configured")

    try:
        # Add timeout to prevent hanging requests
        response = await asyncio.wait_for(
            provider_router.acompletion(**params),
            timeout=REQUEST_TIMEOUT
        )
        
        # Record success for circuit breaker
        _record_success(resolved_model_name)
        logger.debug(f"Successfully received API response from {model_name}")
        
        # Check if streaming
        is_streaming = params.get('stream', False)
        
        if not is_streaming and hasattr(response, 'usage'):
            usage = response.usage
            cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
            cache_read = getattr(usage, 'cache_read_input_tokens', 0)
            total_tokens = getattr(usage, 'prompt_tokens', 0)
            
            if cache_creation > 0 or cache_read > 0:
                logger.info(f"🎯 CACHE METRICS: creation={cache_creation}, read={cache_read}, total={total_tokens}")
            else:
                logger.warning(f"⚠️ NO CACHE USED: total_tokens={total_tokens}")
        elif is_streaming:
            logger.info(f"📡 Streaming response - cache metrics will be in final chunk")
        
        return response

    except asyncio.TimeoutError:
        error_msg = f"Request timeout after {REQUEST_TIMEOUT}s for {model_name}"
        logger.error(error_msg)
        _record_failure(resolved_model_name)
        raise LLMTimeoutError(error_msg)
    
    except Exception as e:
        # Classify and record the error
        classified_error = _classify_error(e)
        _record_failure(resolved_model_name)
        
        logger.error(f"Primary model {model_name} failed: {str(e)}")
        logger.info(f"🔄 Fallback mechanism will be triggered by LiteLLM Router")
        
        # Re-raise the classified error
        raise classified_error

setup_api_keys()
setup_provider_router()
