"""
Simple test script to verify the agent can be imported and initialized
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing Security AI Agent BRAMA...")
print("=" * 50)

# Check API keys
print("\n1. Checking API Keys:")
api_keys = {
    "OPENAI_API_KEY": os.environ.get('OPENAI_API_KEY'),
    "VT_API_KEY": os.environ.get('VT_API_KEY'),
    "SERPER_API_KEY": os.environ.get('SERPER_API_KEY'),
    "URL_HAUSE_KEY": os.environ.get('URL_HAUSE_KEY')
}

for key, value in api_keys.items():
    if value and value != f"your_{key.lower()}":
        print(f"   ✓ {key}: Set")
    else:
        print(f"   ✗ {key}: Not set or using placeholder")

print("\n2. Testing imports:")
try:
    from agent import CybersecurityAgent
    print("   ✓ Agent module imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import agent: {e}")
    exit(1)

print("\n3. Testing agent initialization:")
try:
    # This will fail if API keys are not set, but that's expected
    agent = CybersecurityAgent()
    print("   ✓ Agent initialized successfully!")
    print("\n" + "=" * 50)
    print("SUCCESS! The agent is ready to use.")
    print("Run 'python agent.py' to start the interactive agent.")
except ValueError as e:
    print(f"   ⚠ Agent needs API keys: {e}")
    print("\n" + "=" * 50)
    print("SETUP REQUIRED: Please add your API keys to the .env file")
    print("\nRequired API keys:")
    print("  1. OPENAI_API_KEY - https://platform.openai.com/api-keys")
    print("  2. VT_API_KEY - https://www.virustotal.com/gui/my-apikey")
    print("  3. SERPER_API_KEY - https://serper.dev/api-key")
    print("  4. URL_HAUSE_KEY - https://auth.abuse.ch/")
except Exception as e:
    print(f"   ✗ Unexpected error: {e}")
    exit(1)
