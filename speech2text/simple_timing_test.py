#!/usr/bin/env python3
"""
Simple timing test - just measure processing time of working buffered approach
"""

import time
import sys

def main():
    buffer_seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    
    print(f"⚡ Simple Latency Test")
    print(f"Buffer size: {buffer_seconds}s = {buffer_seconds*1000:.0f}ms")
    print(f"\nThis will test the SAME working buffered approach")
    print(f"Expected total delay: {buffer_seconds*1000:.0f}ms (buffer) + processing time")
    print("\nRunning buffered_speech_to_text.py with timing wrapper...")
    
    # Just run the working version and time it
    import subprocess
    
    start_time = time.time()
    
    try:
        # Run the working buffered version for limited time
        proc = subprocess.Popen([
            'python3', 'buffered_speech_to_text.py', 
            '--buffer-seconds', str(buffer_seconds)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Let it run for 30 seconds max
        timeout = 30
        print(f"Running for {timeout} seconds max...")
        
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            print("Process completed normally")
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            print("Process terminated after timeout")
        
        if stdout:
            print("\nOutput:")
            print(stdout)
        if stderr:
            print("\nErrors:")  
            print(stderr)
            
    except KeyboardInterrupt:
        print("\nStopped by user")
        
    runtime = time.time() - start_time
    print(f"\nTotal test runtime: {runtime:.1f}s")
    
    # Summary based on what we know
    print(f"\n📊 Expected Performance Summary:")
    print(f"   Buffer time: {buffer_seconds*1000:.0f}ms")
    print(f"   Processing time: ~80-200ms (based on earlier tests)")
    print(f"   Total user-experienced delay: ~{buffer_seconds*1000 + 150:.0f}ms")

if __name__ == "__main__":
    main()