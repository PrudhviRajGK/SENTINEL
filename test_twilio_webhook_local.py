"""
Local Twilio Webhook Tester
Simulates Twilio webhook calls without needing ngrok
Tests the omnichannel integration locally
"""

import requests
import json

# Your Twilio credentials
TWILIO_ACCOUNT_SID = 'ACb2e8279a46e0bb45e8a7b46c2e867980'
TWILIO_AUTH_TOKEN = '[AuthToken]'  # Replace with your actual auth token
TWILIO_SANDBOX_NUMBER = 'whatsapp:+14155238886'
YOUR_WHATSAPP = 'whatsapp:+918279407849'

# Local backend URL
BACKEND_URL = 'http://localhost:5000'

def test_webhook_locally():
    """
    Simulate a Twilio webhook call to your local backend
    This tests the /api/omnichannel/twilio/inbound endpoint
    """
    
    print("\n" + "="*60)
    print("TESTING TWILIO WEBHOOK LOCALLY")
    print("="*60)
    
    # Simulate Twilio webhook data (what Twilio sends when user messages you)
    webhook_data = {
        'From': YOUR_WHATSAPP,
        'To': TWILIO_SANDBOX_NUMBER,
        'Body': 'Check https://example.com',
        'MessageSid': 'SM_TEST_123456',
        'AccountSid': TWILIO_ACCOUNT_SID
    }
    
    print("\n1. Simulating incoming WhatsApp message:")
    print(f"   From: {YOUR_WHATSAPP}")
    print(f"   Message: {webhook_data['Body']}")
    
    try:
        # Make request to your local webhook endpoint
        response = requests.post(
            f'{BACKEND_URL}/api/omnichannel/twilio/inbound',
            data=webhook_data,
            timeout=30
        )
        
        print(f"\n2. Backend Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Webhook processed successfully!")
            print("\nNote: In production, Twilio would send the response back to user.")
            print("Check your backend logs to see the agent's analysis.")
        else:
            print(f"\n❌ ERROR: Webhook returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend")
        print("   Make sure backend is running: python app.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def test_multiple_scenarios():
    """Test various message scenarios"""
    
    print("\n" + "="*60)
    print("TESTING MULTIPLE SCENARIOS")
    print("="*60)
    
    test_cases = [
        {
            'name': 'URL Analysis',
            'body': 'Analyze https://suspicious-site.com',
            'expected': 'Risk analysis'
        },
        {
            'name': 'Phone Number Analysis',
            'body': 'Check +1-800-123-4567',
            'expected': 'Phone analysis'
        },
        {
            'name': 'Hindi Message',
            'body': 'इस URL को चेक करें https://example.com',
            'expected': 'Hindi response'
        },
        {
            'name': 'Follow-up Question',
            'body': 'what should I do?',
            'expected': 'Contextual response'
        },
        {
            'name': 'Empty Message',
            'body': '',
            'expected': 'Prompt for input'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['name']}")
        print(f"   Message: {test['body']}")
        
        webhook_data = {
            'From': YOUR_WHATSAPP,
            'To': TWILIO_SANDBOX_NUMBER,
            'Body': test['body'],
            'MessageSid': f'SM_TEST_{i}',
            'AccountSid': TWILIO_ACCOUNT_SID
        }
        
        try:
            response = requests.post(
                f'{BACKEND_URL}/api/omnichannel/twilio/inbound',
                data=webhook_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✓ Status: {response.status_code}")
                print(f"   Expected: {test['expected']}")
            else:
                print(f"   ✗ Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")

def send_test_message_via_twilio():
    """
    Actually send a test message via Twilio
    This will trigger the real webhook if configured
    """
    
    print("\n" + "="*60)
    print("SENDING REAL TEST MESSAGE VIA TWILIO")
    print("="*60)
    
    try:
        from twilio.rest import Client
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send a test message to yourself
        # This will trigger your webhook if it's configured
        message = client.messages.create(
            from_=TWILIO_SANDBOX_NUMBER,
            body='Test message from Sentinel - Reply with a URL to analyze',
            to=YOUR_WHATSAPP
        )
        
        print(f"\n✅ Message sent successfully!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        print("\nNow reply to this message with a URL to test the webhook.")
        
    except ImportError:
        print("\n❌ Twilio library not installed")
        print("   Run: pip install twilio")
    except Exception as e:
        print(f"\n❌ Error sending message: {e}")

def check_backend_status():
    """Check if backend is running and omnichannel is enabled"""
    
    print("\n" + "="*60)
    print("CHECKING BACKEND STATUS")
    print("="*60)
    
    try:
        # Check health
        response = requests.get(f'{BACKEND_URL}/api/health', timeout=5)
        health = response.json()
        
        print(f"\n✓ Backend is running")
        print(f"  Agent initialized: {health.get('agent_initialized')}")
        
        # Check omnichannel status
        response = requests.get(f'{BACKEND_URL}/api/omnichannel/status', timeout=5)
        status = response.json()
        
        print(f"\nOmnichannel Status:")
        print(f"  Web: {'✓' if status.get('web') else '✗'}")
        print(f"  SMS: {'✓' if status.get('sms') else '✗'}")
        print(f"  WhatsApp: {'✓' if status.get('whatsapp') else '✗'}")
        
        if not status.get('sms'):
            print("\n⚠ Twilio not configured. Add credentials to .env:")
            print("  TWILIO_ACCOUNT_SID=your_sid")
            print("  TWILIO_AUTH_TOKEN=your_token")
            print("  TWILIO_PHONE_NUMBER=your_number")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Backend is not running")
        print("   Start it with: python app.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def main():
    """Main test runner"""
    
    print("\n" + "="*70)
    print(" SENTINEL OMNICHANNEL - LOCAL TESTING TOOL")
    print("="*70)
    
    print("\nThis tool tests the Twilio webhook integration without needing ngrok.")
    print("It simulates webhook calls to your local backend.")
    
    # Check backend first
    if not check_backend_status():
        print("\n⚠ Please start the backend first: python app.py")
        return
    
    print("\n" + "="*70)
    print("SELECT TEST MODE:")
    print("="*70)
    print("\n1. Test single webhook call (simulated)")
    print("2. Test multiple scenarios (simulated)")
    print("3. Send real message via Twilio (requires webhook setup)")
    print("4. Check backend status only")
    print("5. Run all tests")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '1':
        test_webhook_locally()
    elif choice == '2':
        test_multiple_scenarios()
    elif choice == '3':
        send_test_message_via_twilio()
    elif choice == '4':
        check_backend_status()
    elif choice == '5':
        check_backend_status()
        test_webhook_locally()
        test_multiple_scenarios()
    else:
        print("\nInvalid choice")
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)
    print("\nFor production use:")
    print("1. Deploy backend to a service with HTTPS (Heroku, Railway, etc.)")
    print("2. Configure Twilio webhook URL to point to your deployment")
    print("3. Or use ngrok for local testing: ngrok http 5000")
    print("\nSee OMNICHANNEL_GUIDE.md for detailed instructions.")

if __name__ == "__main__":
    main()
