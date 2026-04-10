"""Utility functions for OpenAI session management and Twilio communication."""

import json
import ssl
from typing import Any
from fastapi import WebSocket
import websockets

from config import OPENAI_API_KEY, SYSTEM_MESSAGE, VOICE


def create_ssl_context() -> ssl.SSLContext:
    """Create SSL context with certificate verification disabled for testing."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


async def initialize_session(openai_ws: websockets.WebSocketClientProtocol) -> None:
    """
    Initialize OpenAI Realtime API session with configuration.
    
    Args:
        openai_ws: WebSocket connection to OpenAI
    """
    session_update = {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": "gpt-realtime",
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    "turn_detection": {"type": "server_vad"}
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": VOICE
                }
            },
            "instructions": SYSTEM_MESSAGE,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))


async def send_initial_conversation_item(openai_ws: websockets.WebSocketClientProtocol) -> None:
    """
    Send initial conversation item to have AI speak first.
    
    Args:
        openai_ws: WebSocket connection to OpenAI
    """
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Greet the user with 'Hello there! I am an AI voice assistant powered by Twilio and the OpenAI Realtime API. You can ask me for facts, jokes, or anything you can imagine. How can I help you?'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def send_greeting_message(
    openai_ws: websockets.WebSocketClientProtocol,
    greeting_text: str
) -> None:
    """
    Send greeting message to OpenAI for playback to caller.
    
    This function creates a conversation item with the greeting text
    and triggers a response to play it back to the caller.
    
    Args:
        openai_ws: WebSocket connection to OpenAI
        greeting_text: Greeting message text to play
        
    Requirements: 1.2, 17.1
    """
    greeting_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"Greet the user with: '{greeting_text}'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(greeting_item))
    
    # Trigger response generation to play the greeting
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def send_mark(connection: WebSocket, stream_sid: str, mark_queue: list[str]) -> None:
    """
    Send a mark event to Twilio to track audio playback.
    
    Args:
        connection: WebSocket connection to Twilio
        stream_sid: Twilio stream session ID
        mark_queue: Queue to track pending marks
    """
    if stream_sid:
        mark_event = {
            "event": "mark",
            "streamSid": stream_sid,
            "mark": {"name": "responsePart"}
        }
        await connection.send_json(mark_event)
        mark_queue.append('responsePart')


async def send_truncate_event(
    openai_ws: websockets.WebSocketClientProtocol,
    item_id: str,
    elapsed_time: int
) -> None:
    """
    Send truncation event to OpenAI to stop current response.
    
    Args:
        openai_ws: WebSocket connection to OpenAI
        item_id: ID of the item to truncate
        elapsed_time: Time elapsed in milliseconds
    """
    truncate_event = {
        "type": "conversation.item.truncate",
        "item_id": item_id,
        "content_index": 0,
        "audio_end_ms": elapsed_time
    }
    await openai_ws.send(json.dumps(truncate_event))


async def clear_twilio_buffer(websocket: WebSocket, stream_sid: str) -> None:
    """
    Clear Twilio's audio buffer.
    
    Args:
        websocket: WebSocket connection to Twilio
        stream_sid: Twilio stream session ID
    """
    await websocket.send_json({
        "event": "clear",
        "streamSid": stream_sid
    })
