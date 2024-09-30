import schedule
import time
from datetime import datetime
import subprocess

def job():
    print("Running upload.py at midnight:", datetime.now())
    # Run the upload.py script
    subprocess.run(['python', 'upload.py'])

# Schedule the job every day at midnight
schedule.every().day.at("00:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
    
