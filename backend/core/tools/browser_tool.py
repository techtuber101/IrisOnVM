from core.agentpress.tool import ToolResult, openapi_schema, usage_example
from core.agentpress.thread_manager import ThreadManager
from core.sandbox.tool_base import SandboxToolsBase
from core.utils.logger import logger
from core.utils.s3_upload_utils import upload_base64_image
import asyncio
import json
import base64
import io
import traceback
import uuid
from datetime import datetime
from typing import Optional
from PIL import Image
from core.utils.config import config

class BrowserTool(SandboxToolsBase):
    """
    Browser Tool for browser automation using local Stagehand API.
    
    This tool provides browser automation capabilities using a local Stagehand API server,
    replacing the sandbox browser tool functionality.
    
    Only 4 core functions that can handle everything:
    - browser_navigate_to: Navigate to URLs
    - browser_act: Perform any action (click, type, scroll, dropdowns etc.)
    - browser_extract_content: Extract content from pages
    - browser_screenshot: Take screenshots
    """


    def __init__(self, project_id: str, thread_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)
        self.thread_id = thread_id

    def _normalize_base64_image(self, base64_string: str) -> tuple[str, Optional[str]]:
        """Strip metadata prefix and whitespace from a base64 image string."""
        if not base64_string:
            return "", None

        base64_string = base64_string.strip()
        mime_type: Optional[str] = None

        if base64_string.startswith('data:'):
            header, _, data = base64_string.partition(',')
            if ';' in header:
                mime_fragment = header.split(';', 1)[0]
                mime_type = mime_fragment.replace('data:', '') or None
            base64_string = data

        # Remove any whitespace/newline characters that may break decoding
        base64_string = base64_string.replace('\n', '').replace('\r', '').strip()
        return base64_string, mime_type

    async def _ensure_screenshot_dir(self) -> str:
        """Ensure the browser screenshot directory exists inside the sandbox."""
        await self._ensure_sandbox()
        screenshot_dir = f"{self.workspace_path}/browser_screenshots"
        try:
            await self.sandbox.fs.create_folder(screenshot_dir, "755")
        except Exception:
            # Folder likely already exists; ignore errors from create_folder
            pass
        return screenshot_dir

    async def _save_screenshot_to_workspace(self, image_bytes: bytes, mime_type: Optional[str]) -> dict:
        """Persist a screenshot to the sandbox workspace for browser previews."""
        screenshot_dir = await self._ensure_screenshot_dir()
        extension = 'png'

        if mime_type:
            lowered = mime_type.lower()
            if 'jpeg' in lowered or 'jpg' in lowered:
                extension = 'jpg'
            elif 'webp' in lowered:
                extension = 'webp'
            elif 'gif' in lowered:
                extension = 'gif'

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"screenshot_{timestamp}_{uuid.uuid4().hex[:6]}.{extension}"
        file_path = f"{screenshot_dir}/{filename}"

        await self.sandbox.fs.upload_file(image_bytes, file_path)

        relative_path = f"browser_screenshots/{filename}"
        workspace_path = f"/workspace/{relative_path}"
        sandbox_url = self.sandbox_url or getattr(self, '_sandbox_url', None)
        image_url = f"{sandbox_url}/{relative_path}" if sandbox_url else None

        return {
            "file_path": workspace_path,
            "preview_url": workspace_path,
            "relative_path": relative_path,
            "image_url": image_url
        }

    async def _handle_screenshot_result(self, screenshot_data: str) -> dict:
        """Validate, persist, and return metadata for a screenshot payload."""
        info: dict = {}

        normalized_data, mime_type = self._normalize_base64_image(screenshot_data)
        if not normalized_data:
            info['error'] = "Base64 string is empty or invalid"
            return info

        is_valid, validation_message = self._validate_base64_image(normalized_data)
        info['validation_message'] = validation_message

        if not is_valid:
            info['error'] = validation_message
            info['base64'] = normalized_data
            return info

        try:
            image_bytes = base64.b64decode(normalized_data, validate=True)
        except Exception as decode_error:
            error_message = f"Base64 decoding failed: {decode_error}"
            logger.error(error_message)
            info['error'] = error_message
            info['base64'] = normalized_data
            return info

        info['mime_type'] = mime_type

        # Try uploading to Supabase storage first for globally accessible URLs
        try:
            uploaded_url = await upload_base64_image(normalized_data)
            info['image_url'] = uploaded_url
            info['storage'] = 'supabase'
        except Exception as upload_error:
            logger.warning(f"Supabase upload failed, falling back to sandbox storage: {upload_error}")
            info['upload_error'] = str(upload_error)

        # Persist inside the sandbox when Supabase upload is unavailable
        if not info.get('image_url'):
            try:
                workspace_info = await self._save_screenshot_to_workspace(image_bytes, mime_type)
                info.update(workspace_info)
                info['storage'] = 'sandbox'
            except Exception as storage_error:
                error_message = f"Failed to store screenshot in sandbox: {storage_error}"
                logger.error(error_message)
                info['error'] = error_message
                info['base64'] = normalized_data
                return info

        # If we still do not have a direct URL, keep the base64 for downstream fallback rendering
        if not info.get('image_url'):
            info['base64'] = normalized_data

        return info
    
    def _validate_base64_image(self, base64_string: str, max_size_mb: int = 10) -> tuple[bool, str]:
        """
        Comprehensive validation of base64 image data.
        
        Args:
            base64_string (str): The base64 encoded image data
            max_size_mb (int): Maximum allowed image size in megabytes
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Check if data exists and has reasonable length
            if not base64_string or len(base64_string.strip()) < 10:
                return False, "Base64 string is empty or too short"
            
            # Remove data URL prefix if present (data:image/jpeg;base64,...)
            base64_string = base64_string.strip()
            if base64_string.startswith('data:'):
                try:
                    base64_string = base64_string.split(',', 1)[1]
                except (IndexError, ValueError):
                    return False, "Invalid data URL format"

            # Remove whitespace/newlines which may be inserted by some providers
            base64_string = base64_string.replace('\n', '').replace('\r', '').strip()
            
            # Check if string contains only valid base64 characters
            # Base64 alphabet: A-Z, a-z, 0-9, +, /, = (padding)
            import re
            if not re.fullmatch(r'[A-Za-z0-9+/]*={0,2}', base64_string):
                return False, "Invalid base64 characters detected"
            
            # Check if base64 string length is valid (must be multiple of 4)
            if len(base64_string) % 4 != 0:
                return False, "Invalid base64 string length"
            
            # Attempt to decode base64
            try:
                image_data = base64.b64decode(base64_string, validate=True)
            except Exception as e:
                return False, f"Base64 decoding failed: {str(e)}"
            
            # Check decoded data size
            if len(image_data) == 0:
                return False, "Decoded image data is empty"
            
            # Check if decoded data size exceeds limit
            max_size_bytes = max_size_mb * 1024 * 1024
            if len(image_data) > max_size_bytes:
                return False, f"Image size ({len(image_data)} bytes) exceeds limit ({max_size_bytes} bytes)"
            
            # Validate that decoded data is actually a valid image using PIL
            try:
                image_stream = io.BytesIO(image_data)
                with Image.open(image_stream) as img:
                    # Verify the image by attempting to load it
                    img.verify()
                    
                    # Check if image format is supported
                    supported_formats = {'JPEG', 'PNG', 'GIF', 'BMP', 'WEBP', 'TIFF'}
                    if img.format not in supported_formats:
                        return False, f"Unsupported image format: {img.format}"
                    
                    return True, "Image validation successful"
                    
            except Exception as e:
                return False, f"Image validation failed: {str(e)}"
                
        except Exception as e:
            return False, f"Image validation error: {str(e)}"
    
    async def _debug_sandbox_services(self) -> str:
        """Debug method to check what services are running in the sandbox"""
        try:
            await self._ensure_sandbox()
            
            # Check what processes are running
            ps_cmd = "ps aux | grep -E '(python|uvicorn|stagehand|node)' | grep -v grep"
            response = await self.sandbox.process.exec(ps_cmd, timeout=10)
            
            processes = response.result if response.exit_code == 0 else "Failed to get process list"
            
            # Check what ports are listening
            netstat_cmd = "netstat -tlnp 2>/dev/null | grep -E ':(8003|8004)' || ss -tlnp 2>/dev/null | grep -E ':(8003|8004)' || echo 'No netstat/ss available'"
            response2 = await self.sandbox.process.exec(netstat_cmd, timeout=10)
            
            ports = response2.result if response2.exit_code == 0 else "Failed to get port list"
            
            debug_info = f"""
            === Sandbox Services Debug Info ===
            Running processes:
            {processes}

            Listening ports:
            {ports}

            === End Debug Info ===
            """
            return debug_info
            
        except Exception as e:
            return f"Error getting debug info: {e}"

    async def _check_stagehand_api_health(self) -> bool:
        """Check if the Stagehand API server is running and accessible"""
        try:
            await self._ensure_sandbox()
            
            
            # Simple health check curl command
            curl_cmd = "curl -s -X GET 'http://localhost:8004/api' -H 'Content-Type: application/json'"
            
            logger.debug(f"Checking Stagehand API health with: {curl_cmd}")
            
            response = await self.sandbox.process.exec(curl_cmd, timeout=10)
            if response.exit_code == 0:
                try:
                    result = json.loads(response.result)
                    if result.get("status") == "healthy":
                        logger.debug("✅ Stagehand API server is running and healthy")
                        return True
                    else:
                        # If the browser api is not healthy, we need to restart the browser api
                        # Pass API key securely as environment variable instead of command line argument
                        env_vars = {"GEMINI_API_KEY": config.GEMINI_API_KEY}

                        response = await self.sandbox.process.exec(
                            "curl -X POST 'http://localhost:8004/api/init' -H 'Content-Type: application/json' -d '{\"api_key\": \"'$GEMINI_API_KEY'\"}'",
                            timeout=90,
                            env=env_vars
                        )
                        if response.exit_code == 0:
                            logger.debug("Stagehand API server restarted successfully")
                            return True
                        else:
                            logger.warning(f"Stagehand API server restart failed: {response.result}")
                            return False
                except json.JSONDecodeError:
                    logger.warning(f"Stagehand API server responded but with invalid JSON: {response.result}")
                    return False
            else:
                logger.warning(f"Stagehand API server health check failed with exit code {response.exit_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking Stagehand API health: {e}")
            return False

    async def _execute_stagehand_api(self, endpoint: str, params: dict = None, method: str = "POST") -> ToolResult:
        """Execute a Stagehand action through the sandbox API"""
        try:
            # Ensure sandbox is initialized
            await self._ensure_sandbox()
            
            # Check if Stagehand API server is running
            stagehand_healthy = await self._check_stagehand_api_health()
            
            if not stagehand_healthy:
                error_msg = "Stagehand API server is not running. Please ensure the Stagehand API server is running. Error: {response}"
                
                # Add debug information
                debug_info = await self._debug_sandbox_services()
                error_msg += f"\n\nDebug information:\n{debug_info}"
                
                logger.error(error_msg)
                return self.fail_response(error_msg)
            
            
            # Build the curl command to call the local Stagehand API
            url = f"http://localhost:8004/api/{endpoint}"  # Fixed localhost as curl runs inside container
            
            if method == "GET" and params:
                query_params = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{url}?{query_params}"
                curl_cmd = f"curl -s -X {method} '{url}' -H 'Content-Type: application/json'"
            else:
                curl_cmd = f"curl -s -X {method} '{url}' -H 'Content-Type: application/json'"
                if params:
                    json_data = json.dumps(params)
                    curl_cmd += f" -d '{json_data}'"
            
            logger.debug(f"\033[95mExecuting curl command:\033[0m\n{curl_cmd}")
            
            response = await self.sandbox.process.exec(curl_cmd, timeout=30)  # Execute curl inside sandbox
            
            if response.exit_code == 0:
                try:
                    result = json.loads(response.result)
                    logger.debug(f"Stagehand API result: {result}")

                    logger.debug("Stagehand API request completed successfully")

                    browser_state_payload = dict(result)

                    if "screenshot_base64" in result:
                        try:
                            screenshot_info = await self._handle_screenshot_result(result["screenshot_base64"])
                        except Exception as screenshot_error:
                            logger.error("Unexpected error while handling screenshot", exc_info=True)
                            screenshot_info = {"error": str(screenshot_error)}

                        # Remove raw base64 from the agent-facing payload
                        result.pop("screenshot_base64", None)

                        if screenshot_info.get("image_url"):
                            result["image_url"] = screenshot_info["image_url"]
                            browser_state_payload["image_url"] = screenshot_info["image_url"]
                            logger.debug(f"Screenshot available at {screenshot_info['image_url']}")

                        if screenshot_info.get("preview_url"):
                            result["preview_url"] = screenshot_info["preview_url"]
                            browser_state_payload["preview_url"] = screenshot_info["preview_url"]

                        if screenshot_info.get("file_path"):
                            browser_state_payload["file_path"] = screenshot_info["file_path"]
                            result["screenshot_file"] = screenshot_info["file_path"]

                        if screenshot_info.get("relative_path"):
                            browser_state_payload["relative_path"] = screenshot_info["relative_path"]
                            result["screenshot_path"] = screenshot_info["relative_path"]

                        if screenshot_info.get("storage"):
                            browser_state_payload["storage"] = screenshot_info["storage"]

                        if screenshot_info.get("validation_message"):
                            browser_state_payload["validation_message"] = screenshot_info["validation_message"]

                        if screenshot_info.get("upload_error") and not screenshot_info.get("image_url"):
                            logger.warning(f"Screenshot upload failed: {screenshot_info['upload_error']}")
                            result["image_upload_error"] = screenshot_info["upload_error"]
                            result["screenshot_issue"] = f"Screenshot upload issue: {screenshot_info['upload_error']}"
                            browser_state_payload["screenshot_upload_error"] = screenshot_info["upload_error"]

                        if screenshot_info.get("error"):
                            logger.warning(f"Screenshot processing issue: {screenshot_info['error']}")
                            result["screenshot_issue"] = screenshot_info["error"]
                            browser_state_payload["screenshot_error"] = screenshot_info["error"]
                            if not screenshot_info.get("image_url"):
                                result["image_validation_error"] = screenshot_info["error"]

                        base64_fallback = screenshot_info.get("base64")
                        if base64_fallback:
                            browser_state_payload["screenshot_base64"] = base64_fallback
                        else:
                            browser_state_payload.pop("screenshot_base64", None)
                    else:
                        browser_state_payload.pop("screenshot_base64", None)

                    browser_state_payload["input"] = params
                    result["input"] = params
                    added_message = await self.thread_manager.add_message(
                        thread_id=self.thread_id,
                        type="browser_state",
                        content=browser_state_payload,
                        is_llm_message=False
                    )

                    # Prepare clean response for agent (filter out internal metadata)
                    # Only include data that's useful for the agent's decision making
                    clean_result = {
                        "success": result.get("success", True),
                        "message": result.get("message", "Stagehand action completed successfully")
                    }

                    # Include only data that actually comes from browserApi.ts
                    if result.get("url"):
                        clean_result["url"] = result["url"]
                    if result.get("title"):
                        clean_result["title"] = result["title"]
                    if result.get("action"):
                        clean_result["action"] = result["action"]
                    if result.get("image_url"):  # This is screenshot_base64 converted to image_url
                        clean_result["image_url"] = result["image_url"]
                    if result.get("preview_url"):
                        clean_result["preview_url"] = result["preview_url"]
                    if result.get("screenshot_path"):
                        clean_result["screenshot_path"] = result["screenshot_path"]
                    if result.get("screenshot_file"):
                        clean_result["screenshot_file"] = result["screenshot_file"]
                    if browser_state_payload.get("storage"):
                        clean_result["image_storage"] = browser_state_payload.get("storage")

                    # Include any error context that's useful for the agent
                    if result.get("image_validation_error"):
                        clean_result["screenshot_issue"] = f"Screenshot processing issue: {result['image_validation_error']}"
                    if result.get("image_upload_error"):
                        clean_result["screenshot_issue"] = f"Screenshot upload issue: {result['image_upload_error']}"
                    if result.get("screenshot_issue"):
                        clean_result["screenshot_issue"] = result["screenshot_issue"]
                    clean_result["message_id"] = added_message.get("message_id")

                    if clean_result.get("success"):
                        return self.success_response(clean_result)
                    else:
                        # Handle error responses with helpful context  
                        error_msg = result.get("error", result.get("message", "Unknown error"))
                        clean_result["message"] = error_msg
                        return self.fail_response(clean_result)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response JSON: {response.result} {e}")
                    return self.fail_response(f"Failed to parse response JSON: {response.result} {e}")
            else:
                # Check if it's a connection error (exit code 7)
                if response.exit_code == 7:
                    error_msg = f"Stagehand API server is not available on port 8004. Please ensure the Stagehand API server is running. Error: {response}"
                    logger.error(error_msg)
                    return self.fail_response(error_msg)
                else:
                    logger.error(f"Stagehand API request failed: {response}")
                    return self.fail_response(f"Stagehand API request failed: {response}")

        except Exception as e:
            logger.error(f"Error executing Stagehand action: {e}")
            logger.debug(traceback.format_exc())
            return self.fail_response(f"Error executing Stagehand action: {e}")

    # Core Functions Only
    
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "browser_navigate_to",
            "description": "Navigate to a specific url",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The url to navigate to"
                    }
                },
                "required": ["url"]
            }
        }
    })
    @usage_example('''
        <function_calls>
        <invoke name="browser_navigate_to">
        <parameter name="url">https://example.com</parameter>
        </invoke>
        </function_calls>
        ''')
    async def browser_navigate_to(self, url: str) -> ToolResult:
        """Navigate to a URL using Stagehand."""
        logger.debug(f"Browser navigating to: {url}")
        return await self._execute_stagehand_api("navigate", {"url": url})
    
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "browser_act",
            "description": "Perform any browser action using natural language description. CRITICAL: This tool automatically provides a screenshot with every action. For data entry actions (filling forms, entering text, selecting options), you MUST review the provided screenshot to verify that displayed values exactly match what was intended. Report mismatches immediately. CRITICAL FILE UPLOAD RULE: ANY action that involves clicking, interacting with, or locating upload buttons, file inputs, resume upload sections, or any element that might trigger a choose file dialog MUST include the filePath parameter with filePath. This includes actions like 'click upload button', 'locate resume section', 'find file input' etc. Always err on the side of caution - if there's any possibility the action might lead to a file dialog, include filePath. This prevents accidental file dialog triggers without proper file handling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform. Examples: 'click the login button', 'fill in the email field with %email%', 'scroll down to see more content', 'select option 2 from the dropdown', 'press Enter', 'go back', 'wait 5 seconds', 'click at coordinates 100,200', 'select United States from the country dropdown'"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variables to use in the action. Variables in the action string are referenced using %variable_name%. These variables are NOT shared with LLM providers for security.",
                        "additionalProperties": {"type": "string"},
                        "default": {}
                    },
                    "iframes": {
                        "type": "boolean",
                        "description": "Whether to include iframe content in the action. Set to true if the target element is inside an iframe.",
                        "default": True
                    },
                    "filePath": {
                        "type": "string",
                        "description": "CRITICAL: REQUIRED for ANY action that might involve file uploads. This includes: clicking upload buttons, locating resume sections, finding file inputs, scrolling to upload areas, or any action that could potentially trigger a file dialog. Always include this parameter when dealing with upload-related elements to prevent accidental file dialog triggers. The tool will automatically handle the file upload after the action is performed.",
                    }
                },
                "required": ["action"]
            }
        }
    })
    @usage_example('''
        <function_calls>
        <invoke name="browser_act">
        <parameter name="action">fill in the login form with %username% and %password%</parameter>
        <parameter name="variables">{"username": "john.doe", "password": "secret123"}</parameter>
        <parameter name="iframes">true</parameter>
        </invoke>
        </function_calls>
        
        <function_calls>
        <invoke name="browser_act">
        <parameter name="action">click on upload resume button</parameter>
        <parameter name="filePath">/workspace/downloads/document.pdf</parameter>
        </invoke>
        </function_calls>
        ''')
    async def browser_act(self, action: str, variables: dict = None, iframes: bool = False, filePath: dict = None) -> ToolResult:
        """Perform any browser action using Stagehand."""
        logger.debug(f"Browser acting: {action} (variables={'***' if variables else None}, iframes={iframes}), filePath={filePath}")
        params = {"action": action, "iframes": iframes, "variables": variables}
        if filePath:
            params["filePath"] = filePath
        return await self._execute_stagehand_api("act", params)
    
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "browser_extract_content",
            "description": "Extract structured content from the current page using Stagehand",
            "parameters": {
                "type": "object",
                "properties": {
                    "instruction": {
                        "type": "string",
                        "description": "What content to extract (e.g., 'extract all product prices', 'get the main heading', 'extract apartment listings with address and price')"
                    },
                    "iframes": {
                        "type": "boolean",
                        "description": "Whether to include iframe content in the extraction. Set to true if the target content is inside an iframe.",
                        "default": True
                    }
                },
                "required": ["instruction"]
            }
        }
    })
    @usage_example('''
        <function_calls>
        <invoke name="browser_extract_content">
        <parameter name="instruction">extract all product names and prices from the main product list</parameter>
        <parameter name="iframes">true</parameter>
        </invoke>
        </function_calls>
        ''')
    async def browser_extract_content(self, instruction: str, iframes: bool = False) -> ToolResult:
        """Extract structured content from the current page using Stagehand."""
        logger.debug(f"Browser extracting: {instruction} (iframes={iframes})")
        params = {"instruction": instruction, "iframes": iframes}
        return await self._execute_stagehand_api("extract", params)
    
    @openapi_schema({
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": "Take a screenshot of the current page",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name for the screenshot",
                        "default": "screenshot"
                    }
                }
            }
        }
    })
    @usage_example('''
        <function_calls>
        <invoke name="browser_screenshot">
        <parameter name="name">page_screenshot</parameter>
        </invoke>
        </function_calls>
        ''')
    async def browser_screenshot(self, name: str = "screenshot") -> ToolResult:
        """Take a screenshot using Stagehand."""
        logger.debug(f"Browser taking screenshot: {name}")
        return await self._execute_stagehand_api("screenshot", {"name": name})
