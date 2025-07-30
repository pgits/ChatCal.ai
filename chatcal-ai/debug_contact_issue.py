#!/usr/bin/env python3
"""Debug why contact information isn't working."""

import sys
sys.path.append('/Users/petergits/dev/chatCal.ai/chatcal-ai')

from app.core.agent import ChatCalAgent
from app.config import settings
from app.personality.prompts import SYSTEM_PROMPT

def debug_contact_issue():
    print("=== DEBUGGING CONTACT INFORMATION ISSUE ===\n")
    
    # 1. Check settings
    print("1. Settings Check:")
    print(f"   Phone: {settings.my_phone_number}")
    print(f"   Email: {settings.my_email_address}")
    print()
    
    # 2. Check system prompt formatting
    print("2. System Prompt Formatting:")
    try:
        formatted_prompt = SYSTEM_PROMPT.format(
            my_phone_number=settings.my_phone_number,
            my_email_address=settings.my_email_address
        )
        print(f"   ✅ Formatting successful")
        print(f"   Contains phone: {'16302097542' in formatted_prompt}")
        contact_section_present = "Peter's Contact Information" in formatted_prompt
        print(f"   Contains 'Peter's Contact Information': {contact_section_present}")
        print()
        
        # Show the relevant section
        if "Peter's Contact Information" in formatted_prompt:
            start = formatted_prompt.find("Peter's Contact Information")
            section = formatted_prompt[start:start+400]
            print("   Contact section:")
            print(f"   {section}")
            print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # 3. Test agent creation
    print("3. Agent Creation Test:")
    try:
        agent = ChatCalAgent("debug_session")
        print("   ✅ Agent created successfully")
        
        # Test the enhanced system prompt
        user_context = agent._get_user_context()
        from app.personality.prompts import SYSTEM_PROMPT
        system_prompt_with_contacts = SYSTEM_PROMPT.format(
            my_phone_number=settings.my_phone_number,
            my_email_address=settings.my_email_address
        )
        
        enhanced_system_prompt = f"""{system_prompt_with_contacts}

{user_context}"""
        
        print(f"   Enhanced prompt length: {len(enhanced_system_prompt)} chars")
        print(f"   Contains phone in enhanced: {'16302097542' in enhanced_system_prompt}")
        print()
        
        # Test direct LLM call
        print("4. Direct LLM Test:")
        llm = agent.llm
        print(f"   LLM type: {type(llm)}")
        
        # Test a simple complete call with contact info
        test_prompt = f"""You are a helpful assistant. Peter's phone number is {settings.my_phone_number}. 
        
        User asks: What is Peter's phone number?
        
        Response:"""
        
        response = llm.complete(test_prompt)
        print(f"   Direct LLM response: {response.text[:200]}...")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_contact_issue()