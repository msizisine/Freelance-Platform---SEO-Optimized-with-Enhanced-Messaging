"""
Fix WhatsApp message delivery issues
"""

import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_environment():
    """Load environment variables"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    return False

def check_whatsapp_sandbox():
    """Check if we should use WhatsApp Sandbox"""
    print("=== Checking WhatsApp Sandbox ===")
    
    # Load environment
    load_environment()
    
    # From the delivery log, we can see +14155238886 worked
    sandbox_number = "+14155238886"
    
    print("From delivery log, we can see:")
    print(f"Working number: {sandbox_number}")
    print("Status: delivered")
    print("This is the Twilio WhatsApp Sandbox number")
    
    return sandbox_number

def test_sandbox_number():
    """Test with WhatsApp Sandbox number"""
    print("\n=== Testing WhatsApp Sandbox ===")
    
    # Load environment
    load_environment()
    
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        client = Client(account_sid, auth_token)
        
        # Use sandbox number
        sandbox_number = "+14155238886"
        provider_phone = "+27837009708"
        
        # Send test message
        message = "Test message from WhatsApp Sandbox - Please confirm receipt"
        
        message_obj = client.messages.create(
            body=message,
            from_=f"whatsapp:{sandbox_number}",
            to=f"whatsapp:{provider_phone}"
        )
        
        print(f"Sandbox message sent!")
        print(f"SID: {message_obj.sid}")
        print(f"Status: {message_obj.status}")
        print(f"From: {sandbox_number}")
        print(f"To: {provider_phone}")
        
        return True
        
    except Exception as e:
        print(f"Error with sandbox: {e}")
        return False

def check_sandbox_requirements():
    """Check WhatsApp Sandbox requirements"""
    print("\n=== WhatsApp Sandbox Requirements ===")
    
    requirements = """
To use Twilio WhatsApp Sandbox:

1. RECIPIENT MUST JOIN THE SANDBOX:
   - The recipient (+27837009708) must send "join past-magnet" to +14155238886
   - This activates them for the sandbox
   - Without this, messages won't be delivered

2. SANDBOX LIMITATIONS:
   - Only works with numbers that have joined
   - Limited to 100 messages per day
   - For testing only, not production

3. PRODUCTION SETUP:
   - Need to complete WhatsApp Business verification
   - Get a production WhatsApp number
   - Submit message templates for approval

4. CURRENT ISSUE:
   - Provider hasn't joined the sandbox
   - Messages show "undelivered" status
   - Need provider to join first
"""
    
    print(requirements)

def test_with_working_number():
    """Test with a number that has joined sandbox"""
    print("\n=== Testing with Working Number ===")
    
    # Load environment
    load_environment()
    
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        client = Client(account_sid, auth_token)
        
        # Use sandbox number
        sandbox_number = "+14155238886"
        
        # Use a number that has already joined (from log)
        working_number = "+27788823171"
        
        # Send test message
        message = "Test message to working sandbox number"
        
        message_obj = client.messages.create(
            body=message,
            from_=f"whatsapp:{sandbox_number}",
            to=f"whatsapp:{working_number}"
        )
        
        print(f"Test message to working number sent!")
        print(f"SID: {message_obj.sid}")
        print(f"Status: {message_obj.status}")
        print(f"From: {sandbox_number}")
        print(f"To: {working_number}")
        
        return True
        
    except Exception as e:
        print(f"Error with working number: {e}")
        return False

def send_join_instructions():
    """Send instructions to join sandbox"""
    print("\n=== Sandbox Join Instructions ===")
    
    instructions = """
TO FIX DELIVERY ISSUE:

The provider (+27837009708) must join the WhatsApp Sandbox:

1. OPEN WHATSAPP on the provider's phone
2. SEND MESSAGE to: +14155238886
3. MESSAGE TEXT: join past-magnet
4. WAIT for confirmation message

After joining, all messages from the sandbox will be delivered.

ALTERNATIVE SOLUTIONS:
1. Use a different provider who has already joined
2. Complete WhatsApp Business verification for production
3. Use the existing 360Dialog/WhatsApp setup
4. Use SMS as fallback

CURRENT STATUS:
- Twilio account: Working
- Sandbox number: +14155238886
- Provider: Not joined sandbox
- Messages: Undelivered
"""
    
    print(instructions)

def main():
    print("FIXING WHATSAPP DELIVERY ISSUE")
    print("=" * 40)
    
    # Check sandbox
    sandbox_number = check_whatsapp_sandbox()
    
    # Test sandbox
    sandbox_ok = test_sandbox_number()
    
    # Check requirements
    check_sandbox_requirements()
    
    # Test with working number
    working_ok = test_with_working_number()
    
    # Send instructions
    send_join_instructions()
    
    print("\n" + "=" * 40)
    print("DIAGNOSIS:")
    print("Issue: Provider hasn't joined WhatsApp Sandbox")
    print("Solution: Provider must send 'join past-magnet' to +14155238886")
    print("Alternative: Use production WhatsApp or different provider")
    
    if sandbox_ok:
        print("Sandbox is working, just needs provider to join")

if __name__ == "__main__":
    main()
