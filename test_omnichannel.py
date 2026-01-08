"""
Omnichannel Integration Test Suite
Tests Twilio service components without requiring live Twilio connection
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.twilio_client import TwilioService, ConversationMemory
import time

def test_conversation_memory():
    """Test conversation memory functionality"""
    print("\n=== Testing Conversation Memory ===")
    
    memory = ConversationMemory(timeout_minutes=1)  # 1 min for testing
    
    # Test session creation
    memory.update_session(
        phone_number="+1234567890",
        message="Check https://example.com",
        response="Risk: LOW (15%)",
        context={'last_risk': 'low'}
    )
    
    session = memory.get_session("+1234567890")
    assert session is not None, "Session should exist"
    assert len(session['history']) == 1, "Should have 1 exchange"
    print("✓ Session creation works")
    
    # Test context retrieval
    context = memory.get_context_summary("+1234567890")
    assert "Check https://example.com" in context, "Context should contain user message"
    print("✓ Context retrieval works")
    
    # Test multiple exchanges
    for i in range(6):
        memory.update_session(
            phone_number="+1234567890",
            message=f"Message {i}",
            response=f"Response {i}"
        )
    
    session = memory.get_session("+1234567890")
    assert len(session['history']) == 5, "Should keep only last 5 exchanges"
    print("✓ History limiting works (keeps last 5)")
    
    # Test expiry
    print("  Waiting for session to expire (1 min)...")
    time.sleep(61)
    session = memory.get_session("+1234567890")
    assert session is None, "Session should be expired"
    print("✓ Session expiry works")
    
    print("✅ Conversation Memory: ALL TESTS PASSED\n")

def test_language_detection():
    """Test language detection"""
    print("\n=== Testing Language Detection ===")
    
    service = TwilioService()
    
    # Test English
    lang = service.detect_language("Check this URL please")
    assert lang == 'en', f"Should detect English, got {lang}"
    print("✓ English detection works")
    
    # Test Hindi
    lang = service.detect_language("इस URL को चेक करें")
    assert lang == 'hi', f"Should detect Hindi, got {lang}"
    print("✓ Hindi detection works")
    
    # Test mixed (should default to dominant)
    lang = service.detect_language("Check इस URL")
    print(f"  Mixed language detected as: {lang}")
    
    # Test empty
    lang = service.detect_language("")
    assert lang == 'en', "Empty should default to English"
    print("✓ Empty string defaults to English")
    
    print("✅ Language Detection: ALL TESTS PASSED\n")

def test_message_normalization():
    """Test message normalization"""
    print("\n=== Testing Message Normalization ===")
    
    service = TwilioService()
    
    # Mock Twilio message data
    message_data = {
        'from': '+1234567890',
        'to': '+0987654321',
        'body': 'Check https://example.com',
        'message_sid': 'SM123',
        'channel': 'sms'
    }
    
    normalized = service.normalize_message(message_data, context_summary="Previous context")
    
    assert normalized['input'] == 'Check https://example.com', "Input should match body"
    assert normalized['source'] == 'twilio', "Source should be twilio"
    assert normalized['channel'] == 'sms', "Channel should be sms"
    assert normalized['user_id'] == '+1234567890', "User ID should be sender"
    assert normalized['language'] == 'en', "Should detect English"
    assert 'risk_domain' in normalized['context'], "Should have risk domain"
    print("✓ Message normalization works")
    
    # Test Hindi message
    message_data['body'] = 'इस URL को चेक करें'
    normalized = service.normalize_message(message_data)
    assert normalized['language'] == 'hi', "Should detect Hindi"
    print("✓ Hindi message normalization works")
    
    print("✅ Message Normalization: ALL TESTS PASSED\n")

def test_response_formatting():
    """Test SMS response formatting"""
    print("\n=== Testing Response Formatting ===")
    
    service = TwilioService()
    
    # Mock agent result
    agent_result = {
        'risk_level': 'high',
        'confidence': 87,
        'summary': 'This URL shows multiple threat indicators. Listed in URLhaus malware database. 15/70 VirusTotal engines flagged as malicious. Do not visit or share this link.'
    }
    
    # Test English
    response = service.format_response_for_sms(agent_result, language='en')
    assert 'Risk: HIGH' in response, "Should contain risk level"
    assert '87%' in response, "Should contain confidence"
    assert len(response) < 350, f"Should be concise for SMS, got {len(response)} chars"
    print(f"✓ English response formatted ({len(response)} chars)")
    print(f"  Preview: {response[:80]}...")
    
    # Test Hindi
    response = service.format_response_for_sms(agent_result, language='hi')
    assert 'जोखिम:' in response, "Should contain Hindi risk label"
    assert '87%' in response, "Should contain confidence"
    print(f"✓ Hindi response formatted ({len(response)} chars)")
    print(f"  Preview: {response[:80]}...")
    
    # Test error case
    error_result = {'error': 'Analysis failed'}
    response = service.format_response_for_sms(error_result, language='en')
    assert 'failed' in response.lower(), "Should contain error message"
    print("✓ Error response formatted")
    
    # Test very long summary (truncation)
    long_result = {
        'risk_level': 'medium',
        'confidence': 65,
        'summary': 'A' * 500  # Very long summary
    }
    response = service.format_response_for_sms(long_result, language='en')
    assert len(response) < 350, "Should truncate long summaries"
    assert '...' in response, "Should indicate truncation"
    print("✓ Long summary truncation works")
    
    print("✅ Response Formatting: ALL TESTS PASSED\n")

def test_twilio_service_initialization():
    """Test Twilio service initialization"""
    print("\n=== Testing Twilio Service Initialization ===")
    
    service = TwilioService()
    
    # Check if credentials are configured
    if service.is_enabled():
        print("✓ Twilio credentials configured")
        print(f"  Account SID: {service.account_sid[:10]}...")
        print(f"  Phone Number: {service.phone_number}")
    else:
        print("⚠ Twilio credentials not configured (expected for testing)")
        print("  Service will be disabled but won't crash")
    
    # Check memory is initialized
    assert service.memory is not None, "Memory should be initialized"
    print("✓ Conversation memory initialized")
    
    print("✅ Service Initialization: PASSED\n")

def test_parse_incoming_message():
    """Test parsing Twilio webhook data"""
    print("\n=== Testing Incoming Message Parsing ===")
    
    service = TwilioService()
    
    # Mock Twilio request data (SMS)
    request_data = {
        'From': '+1234567890',
        'To': '+0987654321',
        'Body': 'Test message',
        'MessageSid': 'SM123456'
    }
    
    parsed = service.parse_incoming_message(request_data)
    assert parsed['from'] == '+1234567890', "Should parse sender"
    assert parsed['body'] == 'Test message', "Should parse body"
    assert parsed['channel'] == 'sms', "Should detect SMS channel"
    print("✓ SMS message parsing works")
    
    # Mock WhatsApp message
    request_data['From'] = 'whatsapp:+1234567890'
    parsed = service.parse_incoming_message(request_data)
    assert parsed['channel'] == 'whatsapp', "Should detect WhatsApp channel"
    print("✓ WhatsApp message parsing works")
    
    print("✅ Message Parsing: ALL TESTS PASSED\n")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("SENTINEL OMNICHANNEL INTEGRATION TEST SUITE")
    print("="*60)
    
    try:
        test_twilio_service_initialization()
        test_conversation_memory()
        test_language_detection()
        test_message_normalization()
        test_response_formatting()
        test_parse_incoming_message()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nOmnichannel integration is working correctly!")
        print("\nNext steps:")
        print("1. Add Twilio credentials to .env")
        print("2. Start backend: python app.py")
        print("3. Start ngrok: ngrok http 5000")
        print("4. Configure Twilio webhook")
        print("5. Send test SMS")
        print("\nSee OMNICHANNEL_GUIDE.md for detailed instructions.")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
