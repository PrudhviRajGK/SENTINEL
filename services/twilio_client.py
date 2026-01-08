"""
Twilio Client Service
Handles SMS and WhatsApp messaging via Twilio API
Enterprise-grade omnichannel integration
"""

import os
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class ConversationMemory:
    """
    Lightweight conversation memory keyed by phone number
    Automatically expires after timeout
    """
    def __init__(self, timeout_minutes: int = 30):
        self.sessions = {}  # phone_number -> session_data
        self.timeout = timeout_minutes * 60  # Convert to seconds
    
    def get_session(self, phone_number: str) -> Optional[Dict]:
        """Get session data if not expired"""
        if phone_number not in self.sessions:
            return None
        
        session = self.sessions[phone_number]
        
        # Check if expired
        if time.time() - session['last_activity'] > self.timeout:
            del self.sessions[phone_number]
            return None
        
        return session
    
    def update_session(self, phone_number: str, message: str, response: str, context: Dict = None):
        """Update or create session"""
        if phone_number not in self.sessions:
            self.sessions[phone_number] = {
                'history': [],
                'context': context or {},
                'created_at': time.time(),
                'last_activity': time.time()
            }
        
        session = self.sessions[phone_number]
        session['history'].append({
            'user': message,
            'agent': response,
            'timestamp': time.time()
        })
        
        # Keep only last 5 exchanges
        if len(session['history']) > 5:
            session['history'] = session['history'][-5:]
        
        session['last_activity'] = time.time()
        
        # Update context if provided
        if context:
            session['context'].update(context)
    
    def get_context_summary(self, phone_number: str) -> str:
        """Get conversation context for agent"""
        session = self.get_session(phone_number)
        if not session or not session['history']:
            return ""
        
        # Build context from recent history
        context_parts = []
        for exchange in session['history'][-3:]:  # Last 3 exchanges
            context_parts.append(f"User: {exchange['user'][:50]}...")
            context_parts.append(f"Agent: {exchange['agent'][:50]}...")
        
        return "\n".join(context_parts)
    
    def clear_expired(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired = [
            phone for phone, session in self.sessions.items()
            if current_time - session['last_activity'] > self.timeout
        ]
        for phone in expired:
            del self.sessions[phone]

class TwilioService:
    """
    Twilio messaging service for omnichannel support
    Supports SMS and WhatsApp with conversation memory
    """
    
    def __init__(self):
        """
        Initialize Twilio client with credentials from environment
        CRITICAL: Never log or expose credentials
        """
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        self.client = None
        self.enabled = False
        self.memory = ConversationMemory(timeout_minutes=30)
        
        # Only initialize if credentials are present
        if self.account_sid and self.auth_token and self.phone_number:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
            except ImportError:
                print("Warning: Twilio library not installed. SMS/WhatsApp features disabled.")
            except Exception as e:
                print(f"Warning: Twilio initialization failed. SMS/WhatsApp features disabled.")
        else:
            print("Info: Twilio credentials not configured. SMS/WhatsApp features disabled.")
    
    
    def detect_language(self, text: str) -> str:
        """
        Detect language from message text
        Simple heuristic: check for Hindi Unicode characters
        """
        # Check for Devanagari script (Hindi)
        hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        
        # If more than 20% of characters are Hindi, classify as Hindi
        if len(text) > 0 and (hindi_chars / len(text)) > 0.2:
            return 'hi'
        
        return 'en'
    
    def normalize_message(self, message_data: Dict, context_summary: str = "") -> Dict:
        """
        Normalize incoming message into unified agent format
        
        Args:
            message_data: Parsed Twilio message data
            context_summary: Conversation context from memory
        
        Returns:
            Normalized format for agent processing
        """
        user_message = message_data['body']
        sender = message_data['from']
        channel = message_data['channel']
        
        # Detect language
        language = self.detect_language(user_message)
        
        return {
            'input': user_message,
            'source': 'twilio',
            'channel': channel,
            'user_id': sender,
            'language': language,
            'context': {
                'risk_domain': 'social_engineering',
                'conversation_history': context_summary
            }
        }
    
    def format_response_for_sms(self, agent_result: Dict, language: str = 'en') -> str:
        """
        Format agent response for SMS delivery
        Keep concise due to SMS character limits
        
        Args:
            agent_result: Result from agent.agentic_analyze()
            language: Response language
        
        Returns:
            Formatted SMS message (calm, professional, analyst-style)
        """
        # Handle error case
        if 'error' in agent_result:
            if language == 'hi':
                return "विश्लेषण विफल रहा। कृपया पुनः प्रयास करें।"
            return "Analysis failed. Please try again."
        
        risk_level = agent_result.get('risk_level', 'unknown').upper()
        confidence = int(agent_result.get('confidence', 0))
        summary = agent_result.get('summary', agent_result.get('verdict', ''))
        
        # Truncate summary for SMS (aim for ~300 chars total)
        max_summary_length = 200
        if len(summary) > max_summary_length:
            summary = summary[:max_summary_length] + "..."
        
        # Format based on language
        if language == 'hi':
            response = f"जोखिम: {risk_level} ({confidence}%)\n\n{summary}"
        else:
            response = f"Risk: {risk_level} ({confidence}%)\n\n{summary}"
        
        return response
    
    def get_conversation_context(self, phone_number: str) -> str:
        """Get conversation context for phone number"""
        return self.memory.get_context_summary(phone_number)
    
    def update_conversation(self, phone_number: str, user_message: str, agent_response: str, context: Dict = None):
        """Update conversation memory"""
        self.memory.update_session(phone_number, user_message, agent_response, context)
    
    def cleanup_expired_sessions(self):
        """Clean up expired conversation sessions"""
        self.memory.clear_expired()
    
    def send_message(self, to: str, body: str, channel: str = 'sms') -> Dict:
        """
        Send message via Twilio
        
        Args:
            to: Recipient phone number (E.164 format)
            body: Message content
            channel: 'sms' or 'whatsapp'
        
        Returns:
            Dict with status and message_sid or error
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Twilio not configured'
            }
        
        try:
            # Format phone number based on channel
            if channel == 'whatsapp':
                from_number = f'whatsapp:{self.phone_number}'
                to_number = f'whatsapp:{to}' if not to.startswith('whatsapp:') else to
            else:
                from_number = self.phone_number
                to_number = to
            
            # Send message
            message = self.client.messages.create(
                body=body,
                from_=from_number,
                to=to_number
            )
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_incoming_message(self, request_data: Dict) -> Dict:
        """
        Parse incoming Twilio webhook data
        
        Args:
            request_data: Flask request.form or request.values
        
        Returns:
            Normalized message data
        """
        return {
            'from': request_data.get('From', ''),
            'to': request_data.get('To', ''),
            'body': request_data.get('Body', ''),
            'message_sid': request_data.get('MessageSid', ''),
            'channel': 'whatsapp' if 'whatsapp:' in request_data.get('From', '') else 'sms'
        }
    
    def is_enabled(self) -> bool:
        """Check if Twilio is properly configured"""
        return self.enabled
