"""
Create Interactive Twilio WhatsApp Templates with Buttons and Forms
"""

import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_interactive_quotation_template():
    """Create interactive quotation request template"""
    print("=== Creating Interactive Quotation Template ===")
    
    template = """
TEMPLATE: quotation_request_interactive_v1

CATEGORY: UTILITY
LANGUAGE: en
HEADER: Text
HEADER TEXT: New Quotation Request

BODY COMPONENTS:
1. "Quotation ID: {{1}}"
2. "Client: {{2}}"
3. "Title: {{3}}"
4. "Budget: {{4}}"
5. "Location: {{5}}"

FOOTER: This is an automated message from Freelance Platform

BUTTONS:
1. RESPOND {{1}}
   Type: QUICK_REPLY
   ID: respond_{{1}}
   Title: RESPOND {{1}}

2. IGNORE {{1}}
   Type: QUICK_REPLY
   ID: ignore_{{1}}
   Title: IGNORE {{1}}

3. VIEW DETAILS
   Type: QUICK_REPLY
   ID: view_{{1}}
   Title: View Full Details

EXAMPLE USAGE:
Header: "New Quotation Request"
Body: 
  "Quotation ID: 11"
  "Client: msizi@sinengqebo.co.za"
  "Title: Building a wall"
  "Budget: 12500"
  "Location: Edenvale"
Footer: "This is an automated message from Freelance Platform"
Buttons:
  - "RESPOND 11"
  - "IGNORE 11"
  - "View Full Details"
"""
    
    print(template)
    return template

def create_interactive_estimate_template():
    """Create interactive estimate submission template"""
    print("\n=== Creating Interactive Estimate Template ===")
    
    template = """
TEMPLATE: estimate_submission_interactive_v1

CATEGORY: UTILITY
LANGUAGE: en
HEADER: Text
HEADER TEXT: Submit Your Estimate

BODY COMPONENTS:
1. "Quotation: {{1}}"
2. "Title: {{2}}"
3. "Budget: {{3}}"

FOOTER: Choose your submission method below

BUTTONS:
1. WHATSAPP QUICK
   Type: QUICK_REPLY
   ID: whatsapp_quick_{{1}}
   Title: WhatsApp Quick

2. WEB FORM
   Type: QUICK_REPLY
   ID: web_form_{{1}}
   Title: Web Form

3. PHONE CALL
   Type: QUICK_REPLY
   ID: phone_call_{{1}}
   Title: Request Phone Call

EXAMPLE USAGE:
Header: "Submit Your Estimate"
Body:
  "Quotation: 11"
  "Title: Building a wall"
  "Budget: 12500"
Footer: "Choose your submission method below"
Buttons:
  - "WhatsApp Quick"
  - "Web Form"
  - "Request Phone Call"
"""
    
    print(template)
    return template

def create_interactive_form_template():
    """Create interactive form template within WhatsApp"""
    print("\n=== Creating Interactive Form Template ===")
    
    template = """
TEMPLATE: estimate_form_interactive_v1

CATEGORY: UTILITY
LANGUAGE: en
HEADER: Text
HEADER TEXT: Estimate Submission Form

BODY COMPONENTS:
1. "Quotation: {{1}}"
2. "Please provide your estimate details below:"

FOOTER: Complete all fields and submit

BUTTONS:
1. PRICE: R5000
   Type: QUICK_REPLY
   ID: price_5000_{{1}}
   Title: R5000

2. PRICE: R7500
   Type: QUICK_REPLY
   ID: price_7500_{{1}}
   Title: R7500

3. PRICE: R10000
   Type: QUICK_REPLY
   ID: price_10000_{{1}}
   Title: R10000

4. DURATION: 3_days
   Type: QUICK_REPLY
   ID: duration_3days_{{1}}
   Title: 3 Days

5. DURATION: 1_week
   Type: QUICK_REPLY
   ID: duration_1week_{{1}}
   Title: 1 Week

6. DURATION: 2_weeks
   Type: QUICK_REPLY
   ID: duration_2weeks_{{1}}
   Title: 2 Weeks

7. SUBMIT ESTIMATE
   Type: QUICK_REPLY
   ID: submit_{{1}}
   Title: Submit Estimate

8. CANCEL
   Type: QUICK_REPLY
   ID: cancel_{{1}}
   Title: Cancel

INTERACTIVE FLOW:
1. Provider selects price button
2. System asks for duration
3. Provider selects duration button
4. System shows summary
5. Provider confirms with "Submit Estimate"

EXAMPLE INTERACTION:
Provider taps "R7500" -> System asks for duration
Provider taps "1 Week" -> System shows summary
Provider taps "Submit Estimate" -> Estimate submitted
"""
    
    print(template)
    return template

def create_approval_notification_template():
    """Create approval notification template"""
    print("\n=== Creating Approval Notification Template ===")
    
    template = """
TEMPLATE: estimate_approval_interactive_v1

CATEGORY: UTILITY
LANGUAGE: en
HEADER: Text
HEADER TEXT: New Estimate Received!

BODY COMPONENTS:
1. "Quotation: {{1}}"
2. "Provider: {{2}}"
3. "Price: R{{3}}"
4. "Duration: {{4}}"
5. "Submitted: {{5}}"

FOOTER: Review the estimate and respond

BUTTONS:
1. ACCEPT
   Type: QUICK_REPLY
   ID: accept_{{6}}
   Title: Accept Estimate

2. REJECT
   Type: QUICK_REPLY
   ID: reject_{{6}}
   Title: Reject Estimate

3. MESSAGE PROVIDER
   Type: QUICK_REPLY
   ID: message_{{6}}
   Title: Message Provider

4. VIEW DETAILS
   Type: QUICK_REPLY
   ID: view_{{6}}
   Title: View Full Details

EXAMPLE USAGE:
Header: "New Estimate Received!"
Body:
  "Quotation: 11"
  "Provider: msizi34@mobi-cafe.co.za"
  "Price: R7500"
  "Duration: 1 Week"
  "Submitted: 2026-04-11"
Footer: "Review the estimate and respond"
Buttons:
  - "Accept Estimate"
  - "Reject Estimate"
  - "Message Provider"
  - "View Full Details"
"""
    
    print(template)
    return template

def create_template_submission_guide():
    """Create guide for submitting templates to WhatsApp"""
    print("\n=== Template Submission Guide ===")
    
    guide = """
HOW TO SUBMIT INTERACTIVE TEMPLATES TO WHATSAPP:

1. GO TO TWILIO CONSOLE
   - Login to your Twilio account
   - Navigate to Messaging > Senders > WhatsApp Senders

2. CREATE NEW TEMPLATE
   - Click "Create Template" or "Add Template"
   - Select "Interactive" template type
   - Choose "Utility" category

3. FILL TEMPLATE DETAILS
   - Template Name: quotation_request_interactive_v1
   - Language: English (en)
   - Category: Utility

4. ADD COMPONENTS
   - Header: Text, "New Quotation Request"
   - Body: Add 5 body components with {{1}}, {{2}}, etc.
   - Footer: "This is an automated message from Freelance Platform"
   - Buttons: Add 3 quick reply buttons

5. SUBMIT FOR APPROVAL
   - Review template content
   - Submit to WhatsApp for approval
   - Wait 24-48 hours for approval

6. TEST APPROVED TEMPLATE
   - Once approved, test with real phone number
   - Verify buttons work correctly
   - Test interactive flow

IMPORTANT NOTES:
- Template names must be unique
- Variables use {{1}}, {{2}}, {{3}} format
- Button IDs must be unique
- Approval takes 24-48 hours
- Only approved templates can be sent

TEMPLATE VARIABLES:
{{1}} = Quotation ID
{{2}} = Client Name
{{3}} = Title
{{4}} = Budget
{{5}} = Location
{{6}} = Response ID
"""
    
    print(guide)

def create_interactive_service_code():
    """Create code for interactive WhatsApp service"""
    print("\n=== Interactive Service Code ===")
    
    code = '''
# interactive_twilio_service.py
"""
Enhanced Twilio WhatsApp service with interactive templates
"""

import os
import logging
from typing import Dict, Any, List
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django.conf import settings

logger = logging.getLogger(__name__)

class InteractiveTwilioWhatsAppService:
    """Enhanced Twilio WhatsApp service with interactive templates"""
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN')
        self.whatsapp_number = getattr(settings, 'TWILIO_BUSINESS_WHATSAPP_NUMBER')
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_interactive_quotation_request(self, to: str, quotation_id: int, client_name: str, 
                                         title: str, budget: str, location: str) -> Dict[str, Any]:
        """
        Send interactive quotation request with buttons
        
        Args:
            to: Recipient phone number
            quotation_id: Quotation ID
            client_name: Client name
            title: Quotation title
            budget: Budget range
            location: Location
            
        Returns:
            Dict with result
        """
        try:
            # Format phone number
            formatted_to = self._format_phone_number(to)
            
            # Create interactive content
            interactive_content = {
                "type": "button",
                "body": {
                    "text": f"Quotation ID: {quotation_id}\\nClient: {client_name}\\nTitle: {title}\\nBudget: {budget}\\nLocation: {location}"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"respond_{quotation_id}",
                                "title": f"RESPOND {quotation_id}"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"ignore_{quotation_id}",
                                "title": f"IGNORE {quotation_id}"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"view_{quotation_id}",
                                "title": "View Full Details"
                            }
                        }
                    ]
                }
            }
            
            # Send interactive message using approved template
            message_obj = self.client.messages.create(
                from_=f"whatsapp:{self.whatsapp_number}",
                to=f"whatsapp:{formatted_to}",
                content_sid="quotation_request_interactive_v1",
                content_variables={
                    "1": str(quotation_id),
                    "2": client_name,
                    "3": title,
                    "4": budget,
                    "5": location
                }
            )
            
            logger.info(f"Interactive quotation sent: {message_obj.sid}")
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'service': 'interactive_twilio_whatsapp',
                'interactive': True,
                'template': 'quotation_request_interactive_v1',
                'to': formatted_to,
                'status': message_obj.status
            }
            
        except Exception as e:
            logger.error(f"Interactive message error: {e}")
            return {
                'success': False,
                'error': str(e),
                'service': 'interactive_twilio_whatsapp',
                'interactive': True
            }
    
    def send_interactive_estimate_form(self, to: str, quotation_id: int, title: str, budget: str) -> Dict[str, Any]:
        """
        Send interactive estimate form with price and duration options
        
        Args:
            to: Recipient phone number
            quotation_id: Quotation ID
            title: Quotation title
            budget: Budget range
            
        Returns:
            Dict with result
        """
        try:
            # Format phone number
            formatted_to = self._format_phone_number(to)
            
            # Send interactive estimate form
            message_obj = self.client.messages.create(
                from_=f"whatsapp:{self.whatsapp_number}",
                to=f"whatsapp:{formatted_to}",
                content_sid="estimate_form_interactive_v1",
                content_variables={
                    "1": str(quotation_id),
                    "2": title,
                    "3": budget
                }
            )
            
            logger.info(f"Interactive estimate form sent: {message_obj.sid}")
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'service': 'interactive_twilio_whatsapp',
                'interactive': True,
                'template': 'estimate_form_interactive_v1',
                'to': formatted_to,
                'status': message_obj.status
            }
            
        except Exception as e:
            logger.error(f"Interactive form error: {e}")
            return {
                'success': False,
                'error': str(e),
                'service': 'interactive_twilio_whatsapp',
                'interactive': True
            }
    
    def parse_interactive_response(self, sender_phone: str, button_id: str) -> Dict[str, Any]:
        """
        Parse interactive button response
        
        Args:
            sender_phone: Sender's phone number
            button_id: Button ID from interactive response
            
        Returns:
            Dict with parsed action
        """
        try:
            # Parse button ID
            if button_id.startswith("respond_"):
                quotation_id = button_id.split("_")[1]
                return {
                    'action': 'respond',
                    'quotation_id': int(quotation_id),
                    'sender_phone': sender_phone,
                    'next_step': 'show_estimate_form'
                }
            
            elif button_id.startswith("ignore_"):
                quotation_id = button_id.split("_")[1]
                return {
                    'action': 'ignore',
                    'quotation_id': int(quotation_id),
                    'sender_phone': sender_phone,
                    'next_step': 'confirm_ignore'
                }
            
            elif button_id.startswith("view_"):
                quotation_id = button_id.split("_")[1]
                return {
                    'action': 'view',
                    'quotation_id': int(quotation_id),
                    'sender_phone': sender_phone,
                    'next_step': 'send_details'
                }
            
            elif button_id.startswith("price_"):
                parts = button_id.split("_")
                price = parts[1]
                quotation_id = parts[2]
                return {
                    'action': 'select_price',
                    'quotation_id': int(quotation_id),
                    'price': price,
                    'sender_phone': sender_phone,
                    'next_step': 'ask_duration'
                }
            
            elif button_id.startswith("duration_"):
                parts = button_id.split("_")
                duration = parts[1]
                quotation_id = parts[2]
                return {
                    'action': 'select_duration',
                    'quotation_id': int(quotation_id),
                    'duration': duration,
                    'sender_phone': sender_phone,
                    'next_step': 'show_summary'
                }
            
            elif button_id.startswith("submit_"):
                quotation_id = button_id.split("_")[1]
                return {
                    'action': 'submit_estimate',
                    'quotation_id': int(quotation_id),
                    'sender_phone': sender_phone,
                    'next_step': 'save_estimate'
                }
            
            else:
                return {
                    'action': 'unknown',
                    'button_id': button_id,
                    'sender_phone': sender_phone
                }
                
        except Exception as e:
            logger.error(f"Error parsing interactive response: {e}")
            return {
                'action': 'error',
                'error': str(e),
                'button_id': button_id,
                'sender_phone': sender_phone
            }
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for WhatsApp"""
        phone = ''.join(filter(str.isdigit, phone))
        if not phone.startswith('+'):
            if phone.startswith('27'):
                phone = f'+{phone}'
            else:
                phone = f'+{phone}'
        return phone

# Global instance
interactive_twilio_service = InteractiveTwilioWhatsAppService()

def get_interactive_twilio_service() -> InteractiveTwilioWhatsAppService:
    """Get interactive Twilio WhatsApp service instance"""
    return interactive_twilio_service
'''
    
    print(code)
    return code

def main():
    print("CREATING INTERACTIVE TEMPLIO WHATSAPP TEMPLATES")
    print("=" * 50)
    
    # Create templates
    quotation_template = create_interactive_quotation_template()
    estimate_template = create_interactive_estimate_template()
    form_template = create_interactive_form_template()
    approval_template = create_approval_notification_template()
    
    # Create submission guide
    create_template_submission_guide()
    
    # Create service code
    create_interactive_service_code()
    
    print("\n" + "=" * 50)
    print("INTERACTIVE TEMPLATES CREATED!")
    print("\nNEXT STEPS:")
    print("1. Submit templates to WhatsApp for approval")
    print("2. Wait 24-48 hours for approval")
    print("3. Test interactive flow with quotation 11")
    print("4. Provider can tap buttons without sending messages")
    print("5. Complete interactive form within WhatsApp")

if __name__ == "__main__":
    main()
