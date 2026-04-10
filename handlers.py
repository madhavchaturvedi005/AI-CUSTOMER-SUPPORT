"""WebSocket event handlers for Twilio and OpenAI communication with AI features."""

import json
import base64
import asyncio
from typing import Any
from datetime import datetime, timezone
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
import websockets

from config import LOG_EVENT_TYPES, SHOW_TIMING_MATH
from session import SessionState
from utils import send_mark, send_truncate_event, clear_twilio_buffer
from models import Intent


async def receive_from_twilio(
    websocket: WebSocket,
    openai_ws: websockets.WebSocketClientProtocol,
    state: SessionState
) -> None:
    """
    Receive audio data from Twilio and forward it to OpenAI Realtime API.
    
    Args:
        websocket: WebSocket connection to Twilio
        openai_ws: WebSocket connection to OpenAI
        state: Session state object
    """
    print("🎧 receive_from_twilio started")
    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            print(f"📨 Twilio event: {data.get('event', 'unknown')}")
            if data['event'] == 'media' and openai_ws.state.name == 'OPEN':
                state.latest_media_timestamp = int(data['media']['timestamp'])
                audio_append = {
                    "type": "input_audio_buffer.append",
                    "audio": data['media']['payload']
                }
                await openai_ws.send(json.dumps(audio_append))
            elif data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                call_sid = data['start'].get('callSid')  # Get the call SID from the start event
                print(f"Incoming stream has started {stream_sid}")
                if call_sid:
                    print(f"   Associated with call SID: {call_sid}")
                else:
                    print(f"   ⚠️  No callSid in start event! Data: {data['start']}")
                state.reset_on_stream_start(stream_sid)
                # Store call_sid in state for later use
                if call_sid and state.call_manager:
                    state.call_sid = call_sid
                    print(f"   ✅ Stored call_sid in state: {call_sid}")
            elif data['event'] == 'mark':
                if state.mark_queue:
                    state.mark_queue.pop(0)
    except WebSocketDisconnect:
        print("📞 Client disconnected from Twilio")
        if openai_ws.state.name == 'OPEN':
            print("🔌 Closing OpenAI WebSocket...")
            await openai_ws.close()
    finally:
        print("🏁 receive_from_twilio handler completed")


async def send_to_twilio(
    websocket: WebSocket,
    openai_ws: websockets.WebSocketClientProtocol,
    state: SessionState
) -> None:
    """
    Receive events from OpenAI Realtime API and send audio back to Twilio.
    
    Enhanced with AI features:
    - Language detection in first 10 seconds
    - Intent detection with clarification
    - Call routing decisions
    - Conversation history tracking
    
    Args:
        websocket: WebSocket connection to Twilio
        openai_ws: WebSocket connection to OpenAI
        state: Session state object
    """
    print("🎤 send_to_twilio started")
    try:
        async for openai_message in openai_ws:
            # Check if OpenAI WebSocket is still open
            if openai_ws.state.name != 'OPEN':
                print("🔌 OpenAI WebSocket closed, exiting send_to_twilio")
                break
                
            response = json.loads(openai_message)
            if response['type'] in LOG_EVENT_TYPES:
                print(f"Received event: {response['type']}", response)

            # Handle audio output
            if response.get('type') == 'response.output_audio.delta' and 'delta' in response:
                audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                audio_delta = {
                    "event": "media",
                    "streamSid": state.stream_sid,
                    "media": {
                        "payload": audio_payload
                    }
                }
                await websocket.send_json(audio_delta)

                if response.get("item_id") and response["item_id"] != state.last_assistant_item:
                    state.response_start_timestamp_twilio = state.latest_media_timestamp
                    state.last_assistant_item = response["item_id"]
                    if SHOW_TIMING_MATH:
                        print(f"Setting start timestamp for new response: {state.response_start_timestamp_twilio}ms")

                await send_mark(websocket, state.stream_sid, state.mark_queue)
            
            # Handle conversation transcript for AI features
            if response.get('type') == 'conversation.item.created':
                item = response.get('item', {})
                role = item.get('role')
                content = item.get('content', [])
                
                # Extract text from content
                text = ""
                for c in content:
                    if c.get('type') == 'text':
                        text = c.get('text', '')
                    elif c.get('type') == 'input_text':
                        text = c.get('input_text', '')
                
                if text and state.call_manager:
                    # Add to conversation history
                    speaker = "caller" if role == "user" else "assistant"
                    await state.call_manager.add_conversation_turn(
                        state.stream_sid,
                        speaker,
                        text
                    )
                    print(f"💬 {speaker}: {text[:60]}...")
                    
                    # Language detection (first 10 seconds)
                    if state.call_start_time and state.language_manager:
                        elapsed_ms = int((datetime.now(timezone.utc) - state.call_start_time).total_seconds() * 1000)
                        if elapsed_ms <= 10000 and speaker == "caller":
                            detected_lang, confidence = await state.call_manager.detect_and_update_language(
                                state.stream_sid,
                                openai_ws,
                                elapsed_ms
                            )
                            if detected_lang and confidence >= 0.8:
                                print(f"🌍 Language detected: {state.language_manager.get_language_name(detected_lang)} (confidence: {confidence:.2f})")
                    
                    # Intent detection (after caller speaks)
                    if speaker == "caller" and state.intent_detector:
                        try:
                            context = await state.call_manager.get_call_context(state.stream_sid)
                            if context:
                                intent, conf, clarification = await state.call_manager.handle_intent_with_clarification(
                                    state.stream_sid,
                                    state.intent_detector,
                                    context.conversation_history,
                                    text
                                )
                                
                                if intent != Intent.UNKNOWN:
                                    print(f"🎯 Intent detected: {intent.value} (confidence: {conf:.2f})")
                                    
                                    # Check routing decision
                                    if state.call_router:
                                        routing_decision = await state.call_router.route_call(
                                            context,
                                            {}  # No agents available in demo
                                        )
                                        print(f"📞 Routing decision: {routing_decision}")
                                        
                                        if routing_decision.startswith("transfer_to_agent"):
                                            print(f"   → Would transfer to agent (demo mode)")
                                
                                if clarification:
                                    print(f"❓ Clarification needed: {clarification[:60]}...")
                        except Exception as e:
                            print(f"⚠️  Error in intent detection: {e}")
            
            # Handle greeting completion event
            if response.get('type') == 'response.done':
                print("✅ Response completed")
                # Answer the call in our system
                if state.call_manager and state.stream_sid:
                    try:
                        await state.call_manager.answer_call(state.stream_sid)
                    except Exception as e:
                        print(f"⚠️  Error answering call: {e}")

            # Trigger an interruption
            if response.get('type') == 'input_audio_buffer.speech_started':
                print("🗣️  Speech started detected")
                if state.last_assistant_item:
                    print(f"⏸️  Interrupting response with id: {state.last_assistant_item}")
                    await handle_speech_started_event(websocket, openai_ws, state)
    except websockets.exceptions.ConnectionClosed:
        print("🔌 OpenAI WebSocket connection closed")
    except asyncio.CancelledError:
        print("🛑 send_to_twilio task cancelled")
        raise  # Re-raise to properly handle cancellation
    except Exception as e:
        print(f"❌ Error in send_to_twilio: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 send_to_twilio handler completed")


async def handle_speech_started_event(
    websocket: WebSocket,
    openai_ws: websockets.WebSocketClientProtocol,
    state: SessionState
) -> None:
    """
    Handle interruption when the caller's speech starts.
    
    This function implements Requirements 10.1-10.5:
    - 10.1: Detects speech within 300ms (handled by OpenAI's speech_started event)
    - 10.2: Stops AI audio output immediately via truncation
    - 10.3: Clears audio buffer to prevent delayed playback
    - 10.4: Resumes listening automatically (OpenAI handles this)
    - 10.5: Preserves conversation context for appropriate response
    
    The conversation history is maintained in CallManager and SessionState,
    ensuring the AI can generate contextually appropriate responses after interruption.
    
    Args:
        websocket: WebSocket connection to Twilio
        openai_ws: WebSocket connection to OpenAI
        state: Session state object
    """
    print("Handling speech started event.")
    if state.mark_queue and state.response_start_timestamp_twilio is not None:
        elapsed_time = state.latest_media_timestamp - state.response_start_timestamp_twilio
        if SHOW_TIMING_MATH:
            print(f"Calculating elapsed time for truncation: {state.latest_media_timestamp} - {state.response_start_timestamp_twilio} = {elapsed_time}ms")

        if state.last_assistant_item:
            if SHOW_TIMING_MATH:
                print(f"Truncating item with ID: {state.last_assistant_item}, Truncated at: {elapsed_time}ms")

            # Stop AI audio output (Requirement 10.2)
            await send_truncate_event(openai_ws, state.last_assistant_item, elapsed_time)

        # Clear audio buffer (Requirement 10.3)
        await clear_twilio_buffer(websocket, state.stream_sid)
        
        # Clear interruption state while preserving context (Requirement 10.5)
        state.clear_interruption_state()
        
        print("✅ Interruption handled - context preserved, ready for caller input")
