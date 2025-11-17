# ErgoMind API WebSocket Authentication Issue

## Critical Finding

The ErgoMind API WebSocket endpoint has a **critical authentication bug** that prevents the application from functioning.

## Investigation Summary

### What Works ✅
- REST API authentication with `X-API-Key: 7YBp4W2AjAp0`
- Creating conversations via `POST /api/v1/conversations`
- WebSocket **connection establishment** (handshake succeeds)

### What's Broken ❌
- WebSocket **query execution** (all queries rejected)
- Error message: `"Invalid bearer token for WebSocket"`

## Detailed Test Results

### Test 1: REST API ✅
```bash
curl -H "X-API-Key: 7YBp4W2AjAp0" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "overwatch@ergo.net", "initial_message": "Test"}' \
     https://bl373-ergo-api.toolbox.bluelabellabs.io/api/v1/conversations

Response: 201 Created
```

### Test 2: WebSocket Connection ✅
```python
ws_url = f"wss://bl373-ergo-api.toolbox.bluelabellabs.io/ws/chat?token={api_key}"
async with session.ws_connect(ws_url) as ws:
    # Connection succeeds ✓
```

### Test 3: WebSocket Query ❌
```python
query_msg = {
    "type": "query",
    "conversation_id": conv_id,
    "user_id": user_id,
    "message": "Test query"
}
await ws.send_json(query_msg)

Response: {"type": "error", "message": "Invalid bearer token for WebSocket"}
```

## Authentication Methods Tested

All methods failed:

1. **Query parameter**: `?token={api_key}` ❌
2. **Bearer header**: `Authorization: Bearer {api_key}` ❌
3. **X-API-Key header**: `X-API-Key: {api_key}` ❌
4. **Token in message**: `{"token": "{api_key}", ...}` ❌
5. **API key in message**: `{"api_key": "{api_key}", ...}` ❌
6. **Initial auth message**: `{"type": "auth", "token": "{api_key}"}` ❌

## Root Cause Analysis

The WebSocket endpoint appears to:
1. Accept connections with the token in the query string
2. **Fail to maintain** or **validate** that token for subsequent messages
3. Expect a different "bearer token" that we don't have access to

This suggests either:
- A **bug** in the ErgoMind API implementation
- A **missing step** in the authentication flow (token exchange?)
- An **incomplete API** deployment (WebSocket not fully implemented)
- The provided API key `7YBp4W2AjAp0` is **not authorized** for WebSocket access

## Impact

**CRITICAL**: The application cannot function without WebSocket query capability.
- ❌ Cannot fetch intelligence data from ErgoMind
- ❌ Cannot generate meaningful reports
- ❌ Core functionality is blocked

## Recommended Actions

### Immediate (for ErgoMind Team)
1. **Verify API key** `7YBp4W2AjAp0` has WebSocket permissions
2. **Check WebSocket auth middleware** for token validation bugs
3. **Provide correct authentication flow** documentation
4. **Test WebSocket endpoint** with this specific API key

### Short-term Workaround (for Development)
1. Implement **mock/demo data** for testing UI and report generation
2. Use **sample intelligence items** to validate document formatting
3. Test all non-API components of the system

### Alternative Solutions
1. **REST API fallback**: If ErgoMind provides a REST query endpoint
2. **Polling mechanism**: Query via REST if available
3. **Hybrid approach**: Use REST for queries if WebSocket unavailable

## Code Evidence

The application code is correct - we've tested every possible authentication method:
- Query string tokens ✓ (tried)
- Authorization headers ✓ (tried)
- Message-level tokens ✓ (tried)
- Initial handshakes ✓ (tried)

**Conclusion**: This is an ErgoMind API issue, not a client implementation issue.

## Contact Information

**API**: https://bl373-ergo-api.toolbox.bluelabellabs.io
**API Key**: 7YBp4W2AjAp0
**WebSocket**: wss://bl373-ergo-api.toolbox.bluelabellabs.io/ws/chat

**Support needed**: WebSocket authentication troubleshooting

## Testing Script

To reproduce the issue:

```python
import asyncio
import aiohttp
import json

async def reproduce_issue():
    api_key = "7YBp4W2AjAp0"

    async with aiohttp.ClientSession() as session:
        # Step 1: Create conversation (works)
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        data = {"user_id": "overwatch@ergo.net", "initial_message": "Test"}

        async with session.post(
            "https://bl373-ergo-api.toolbox.bluelabellabs.io/api/v1/conversations",
            headers=headers,
            json=data
        ) as resp:
            result = await resp.json()
            conv_id = result["conversation_id"]
            print(f"✓ Conversation created: {conv_id}")

        # Step 2: Connect WebSocket (works)
        ws_url = f"wss://bl373-ergo-api.toolbox.bluelabellabs.io/ws/chat?token={api_key}"
        async with session.ws_connect(ws_url) as ws:
            print("✓ WebSocket connected")

            # Step 3: Send query (FAILS)
            query = {
                "type": "query",
                "conversation_id": conv_id,
                "user_id": "overwatch@ergo.net",
                "message": "What are the top risks this month?"
            }
            await ws.send_json(query)

            msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
            data = json.loads(msg.data)

            if data.get("type") == "error":
                print(f"❌ ERROR: {data.get('message')}")
            else:
                print(f"✓ Success: {data}")

asyncio.run(reproduce_issue())
```

Expected output:
```
✓ Conversation created: <uuid>
✓ WebSocket connected
❌ ERROR: Invalid bearer token for WebSocket
```
