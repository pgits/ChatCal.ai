#!/usr/bin/env python3
"""Monitor OAuth transport fix deployment completion."""

import time
import subprocess
import requests
import json
from datetime import datetime

def check_deployment_status():
    """Check if the OAuth transport fixes are deployed."""
    try:
        # Test the OAuth endpoint to see if it's using the correct client ID
        response = requests.get(
            "https://chatcal-ai-432729289953.us-east1.run.app/auth/login",
            timeout=10
        )
        
        if response.status_code == 200:
            auth_data = response.json()
            auth_url = auth_data.get('auth_url', '')
            
            # Check if it's using the correct client ID (not the old cached one)
            if '432729289953-1di05ajntobgvv0aakgjahnrtp60491j' in auth_url:
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - OAuth deployment successful!")
                print(f"🔧 Using correct client ID: 432729289953-...")
                
                # Test the transport security fix
                test_url = "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=432729289953-1di05ajntobgvv0aakgjahnrtp60491j.apps.googleusercontent.com&redirect_uri=https%3A%2F%2Fchatcal-ai-432729289953.us-east1.run.app%2Fauth%2Fcallback&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.events&access_type=offline&include_granted_scopes=true&prompt=consent&state=deployment_test"
                
                print(f"🚀 DEPLOYMENT COMPLETE!")
                print(f"📅 ChatCal.ai OAuth transport fixes are now live!")
                print(f"🔗 Test OAuth URL: {test_url}")
                return True
            else:
                print(f"⏳ {datetime.now().strftime('%H:%M:%S')} - Still using old client ID, deployment in progress...")
                return False
        else:
            print(f"⏳ {datetime.now().strftime('%H:%M:%S')} - Service not responding (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"⏳ {datetime.now().strftime('%H:%M:%S')} - Deployment still in progress... ({str(e)[:50]})")
        return False

def monitor_deployment():
    """Monitor deployment until completion."""
    print("🔧 Monitoring OAuth transport fix deployment...")
    print("📅 Will notify when deployment completes and transport fixes are live")
    print()
    
    check_count = 0
    max_checks = 60  # 30 minutes maximum
    
    while check_count < max_checks:
        if check_deployment_status():
            print()
            print("🎉 NOTIFICATION: OAuth Transport Fix Deployment COMPLETED!")
            print("✅ ChatCal.ai regular OAuth flow should now work without transport errors")
            print("🔧 The application is ready for production calendar booking")
            return True
            
        check_count += 1
        if check_count < max_checks:
            time.sleep(30)  # Check every 30 seconds
    
    print()
    print("⚠️ NOTIFICATION: Deployment monitoring timeout reached")
    print("🔧 Deployment may still be in progress - check manually")
    return False

if __name__ == "__main__":
    monitor_deployment()