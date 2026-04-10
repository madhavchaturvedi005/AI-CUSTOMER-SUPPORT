"""Monitor server logs in real-time and extract transcripts."""

import subprocess
import time
import re
from collections import deque
from log_analyzer import extract_transcripts_from_logs, save_transcript_to_database


class LiveLogMonitor:
    """Monitor server logs and extract transcripts in real-time."""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer = deque(maxlen=buffer_size)
        self.processed_calls = set()
    
    def process_log_line(self, line: str):
        """Process a single log line."""
        self.buffer.append(line)
        
        # Check if call ended
        if "Call ended, completing call:" in line:
            # Extract call_sid
            match = re.search(r'CA[a-f0-9]+', line)
            if match:
                call_sid = match.group(0)
                if call_sid not in self.processed_calls:
                    print(f"\n🔍 Detected call end: {call_sid}")
                    self.extract_and_save_transcript(call_sid)
                    self.processed_calls.add(call_sid)
    
    def extract_and_save_transcript(self, call_sid: str):
        """Extract transcript for a specific call from buffer."""
        # Get relevant logs for this call
        relevant_logs = [
            line for line in self.buffer
            if call_sid in line or "transcript" in line.lower()
        ]
        
        if not relevant_logs:
            print(f"⚠️  No relevant logs found for {call_sid}")
            return
        
        log_text = "\n".join(relevant_logs)
        print(f"📊 Analyzing {len(log_text)} characters for call {call_sid}...")
        
        # Extract transcript using OpenAI
        result = extract_transcripts_from_logs(log_text)
        
        if result.get('conversation'):
            print(f"✅ Found {len(result['conversation'])} transcript turns")
            # Save to database
            save_transcript_to_database(result)
        else:
            print(f"⚠️  No transcript found in logs")
    
    def monitor_file(self, log_file: str):
        """Monitor a log file for new lines."""
        print(f"👀 Monitoring log file: {log_file}")
        print("Press Ctrl+C to stop\n")
        
        try:
            with open(log_file, 'r') as f:
                # Go to end of file
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        print(line.strip())
                        self.process_log_line(line)
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")
        except FileNotFoundError:
            print(f"❌ Log file not found: {log_file}")
            print("Start your server with: python main.py 2>&1 | tee server.log")


def main():
    """Main entry point."""
    import sys
    
    log_file = sys.argv[1] if len(sys.argv) > 1 else "server.log"
    
    monitor = LiveLogMonitor()
    monitor.monitor_file(log_file)


if __name__ == "__main__":
    main()
