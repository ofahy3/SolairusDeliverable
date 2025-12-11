"""
ErgoMind API Client with Robust WebSocket Handling
Designed to handle the quirks and bugs of the ErgoMind WebSocket implementation
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import backoff
import websockets
from aiohttp import ClientSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ErgoMindConfig:
    """Configuration for ErgoMind API - Requires environment variables"""

    base_url: str = field(
        default_factory=lambda: os.getenv(
            "ERGOMIND_BASE_URL", "https://bl373-ergo-api.toolbox.bluelabellabs.io"
        )
    )
    ws_url: str = field(
        default_factory=lambda: os.getenv(
            "ERGOMIND_WS_URL", "wss://bl373-ergo-api.toolbox.bluelabellabs.io/ws/chat"
        )
    )
    api_key: str = field(default_factory=lambda: os.getenv("ERGOMIND_API_KEY", ""))
    user_id: str = field(default_factory=lambda: os.getenv("ERGOMIND_USER_ID", ""))
    max_retries: int = 5
    timeout: int = 120
    backoff_factor: float = 2.0

    def validate(self) -> bool:
        """Validate that required configuration is present"""
        if not self.api_key:
            logger.error("ERGOMIND_API_KEY environment variable is required")
            return False
        if not self.user_id:
            logger.error("ERGOMIND_USER_ID environment variable is required")
            return False
        return True


@dataclass
class QueryResult:
    """Result from an ErgoMind query"""

    query: str
    response: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None
    confidence_score: float = 0.0


class ErgoMindClient:
    """
    Robust ErgoMind API client with extensive error handling
    """

    def __init__(self, config: Optional[ErgoMindConfig] = None):
        self.config = config or ErgoMindConfig()
        self.session: Optional[ClientSession] = None
        self.conversation_id: Optional[str] = None
        self._response_buffer: List[str] = []

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self):
        """Initialize the HTTP session"""
        if not self.session:
            connector = aiohttp.TCPConnector(force_close=True)
            self.session = ClientSession(connector=connector)

    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None

    @backoff.on_exception(
        backoff.expo, (aiohttp.ClientError, asyncio.TimeoutError), max_tries=3, max_time=60
    )
    async def create_conversation(self, initial_message: str = "Hello") -> str:
        """
        Create a new conversation and return the conversation ID
        """
        url = f"{self.config.base_url}/api/v1/conversations"
        # ErgoMind API requires Bearer token authentication
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "X-API-Key": self.config.api_key,  # Also include X-API-Key as fallback
            "Content-Type": "application/json",
        }
        data = {"user_id": self.config.user_id, "initial_message": initial_message}

        try:
            if self.session is None:
                raise RuntimeError(
                    "Session not initialized. Use async context manager or call initialize()"
                )
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status == 201:
                    result = await response.json()
                    self.conversation_id = result.get("conversation_id")
                    logger.info(f"Created conversation: {self.conversation_id}")
                    return self.conversation_id
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to create conversation: {response.status} - {error_text}"
                    )
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise

    async def query_websocket(
        self, query: str, conversation_id: Optional[str] = None
    ) -> QueryResult:
        """
        Send a query via WebSocket using the proven working pattern
        """
        conv_id = conversation_id or self.conversation_id
        if not conv_id:
            conv_id = await self.create_conversation()

        max_retries = self.config.max_retries
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                logger.info(
                    f"Attempting WebSocket connection (attempt {retry_count + 1}/{max_retries})"
                )
                result = await self._execute_websocket_query(conv_id, query)
                if result.success:
                    return result
                last_error = result.error

            except Exception as e:
                last_error = str(e)
                logger.error(f"WebSocket error on attempt {retry_count + 1}: {e}")

            retry_count += 1
            if retry_count < max_retries:
                wait_time = self.config.backoff_factor**retry_count
                logger.info(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)

        # All retries failed
        return QueryResult(
            query=query,
            response="",
            success=False,
            error=f"Failed after {max_retries} attempts. Last error: {last_error}",
        )

    async def _execute_websocket_query(self, conversation_id: str, query: str) -> QueryResult:
        """
        Execute a single WebSocket query using the proven working pattern
        Uses websockets library with X-API-Key header authentication
        """
        response_chunks = []
        source_documents = []

        try:
            # Connect with X-API-Key header (the working pattern!)
            async with websockets.connect(
                self.config.ws_url,
                extra_headers={"X-API-Key": self.config.api_key},
                ping_interval=20.0,
                ping_timeout=10.0,
                close_timeout=10.0,
            ) as websocket:
                logger.info("WebSocket connected with X-API-Key header")

                # Send query with correct payload structure
                query_payload = {
                    "type": "query",
                    "message": query,
                    "user_id": self.config.user_id,
                    "conversation_id": conversation_id,
                    "max_results": 10,
                    "min_score": 0.0,
                }

                await websocket.send(json.dumps(query_payload))
                logger.info(f"Sent query: {query[:100]}...")

                # Receive streaming response
                start_time = time.time()
                complete = False

                async for message in websocket:
                    # Check timeout
                    if (time.time() - start_time) > self.config.timeout:
                        logger.warning("Query timeout reached")
                        break

                    try:
                        data = json.loads(message)
                        msg_type = data.get("type")

                        # Handle streaming response chunks
                        if msg_type in ("text", "chunk", "delta"):
                            content = data.get("content", "")
                            response_chunks.append(content)
                            logger.info(f"Received {msg_type}: {len(content)} chars")

                        # Handle sources
                        elif msg_type == "sources":
                            sources = data.get("sources", [])
                            source_documents.extend(sources)
                            logger.info(f"Received {len(sources)} sources")

                        # Handle completion
                        elif msg_type in ("done", "complete"):
                            complete = True
                            logger.info("Query complete")
                            break

                        # Handle errors
                        elif msg_type == "error":
                            error_msg = data.get("message", "Unknown error")
                            raise Exception(f"ErgoMind error: {error_msg}")

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
                        continue

                # Assemble final response
                response_text = "".join(response_chunks)

                if not response_text and not complete:
                    raise Exception("No response received before timeout")

                # Calculate confidence
                confidence = self._calculate_confidence(response_text, source_documents)

                return QueryResult(
                    query=query,
                    response=response_text,
                    sources=source_documents,
                    success=True,
                    confidence_score=confidence,
                )

        except Exception as e:
            logger.error(f"WebSocket query failed: {e}")
            return QueryResult(query=query, response="", success=False, error=str(e))

    def _calculate_confidence(self, response: str, sources: List[Dict]) -> float:
        """
        Calculate confidence score for the response
        """
        score = 0.0

        # Check response length
        if len(response) > 100:
            score += 0.3
        if len(response) > 500:
            score += 0.2

        # Check for sources
        if sources:
            score += 0.2
        if len(sources) > 2:
            score += 0.1

        # Check for structured content
        if any(marker in response for marker in ["•", "-", "1.", "2."]):
            score += 0.1

        # Check for specific keywords indicating good content
        quality_markers = ["according to", "analysis", "trend", "forecast", "impact"]
        if any(marker in response.lower() for marker in quality_markers):
            score += 0.1

        return min(score, 1.0)

    async def batch_query(self, queries: List[str]) -> List[QueryResult]:
        """
        Execute multiple queries with rate limiting
        """
        results = []

        for i, query in enumerate(queries):
            logger.info(f"Processing query {i+1}/{len(queries)}")

            result = await self.query_websocket(query)
            results.append(result)

            # Rate limiting between queries
            if i < len(queries) - 1:
                await asyncio.sleep(2)  # 2 second delay between queries

        return results

    async def test_connection(self) -> bool:
        """
        Test the connection to ErgoMind
        """
        try:
            if self.session is None:
                raise RuntimeError(
                    "Session not initialized. Use async context manager or call initialize()"
                )
            # Test REST API
            url = f"{self.config.base_url}/api/v1/health"
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "X-API-Key": self.config.api_key,
            }

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    logger.info("REST API connection successful")
                else:
                    logger.error(f"REST API connection failed: {response.status}")
                    return False

            # Test WebSocket with simple query
            result = await self.query_websocket("Hello, can you confirm connection?")
            if result.success:
                logger.info("WebSocket connection successful")
                return True
            else:
                logger.error(f"WebSocket connection failed: {result.error}")
                return False

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
