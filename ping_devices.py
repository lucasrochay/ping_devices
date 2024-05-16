import json
import os
import subprocess
import time
import threading
from datetime import datetime
import platform

if platform.system() == 'Windows':
    import msvcrt
else:
    import sys

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        print(f"Config file {config_file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {config_file}.")
        sys.exit(1)
    return config

def parse_ping_output(output, system):
    transmitted, received, loss = 0, 0, 0
    if system == 'Windows':
        for line in output.split('\n'):
            if 'Packets: Sent =' in line:
                parts = line.split(',')
                transmitted = int(parts[0].split('=')[1].strip())
                received = int(parts[1].split('=')[1].strip())
                loss_str = parts[2].split('=')[1].strip()
                loss = int(loss_str.split()[0])
    else:
        for line in output.split('\n'):
            if 'packets transmitted' in line:
                parts = line.split(',')
                transmitted = int(parts[0].split()[0])
                received = int(parts[1].split()[0])
                loss = float(parts[2].split()[0].strip('%'))
    return transmitted, received, loss

def ping_device(device, ping_count, timeout, system):
    if system == 'Windows':
        command = ['ping', '-n', str(ping_count), '-w', str(timeout * 1000), device]
    else:
        command = ['ping', '-c', str(ping_count), '-W', str(timeout), device]
        
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Try decoding with utf-8 and handle errors
    try:
        output = result.stdout.decode('utf-8', errors='replace')
    except UnicodeDecodeError:
        output = result.stdout.decode('latin-1', errors='replace')

    transmitted, received, loss = parse_ping_output(output, system)

    return transmitted, received

def ping_devices_continuously(devices, ping_count, timeout, results, stop_event, system):
    while not stop_event.is_set():
        for device in devices:
            print(f"Pinging {device}...")
            transmitted, received = ping_device(device, ping_count, timeout, system)
            results[device]['transmitted'] += transmitted
            results[device]['received'] += received
        time.sleep(1)  # Add a small delay to avoid overwhelming the network

def write_summary_to_log(log_file, results, start_time, end_time):
    with open(log_file, 'a') as log:
        log.write("\nSummary:\n")
        log.write(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for device, stats in results.items():
            transmitted = stats['transmitted']
            received = stats['received']
            lost = transmitted - received
            loss_percentage = (lost / transmitted) * 100 if transmitted > 0 else 100.0
            log.write(f"-- Device: {device} --\n")
            log.write(f"Packets: Sent = {transmitted}, Received = {received}, Lost = {loss_percentage:.1f}%\n")
            log.write("\n")

def wait_for_key_press(stop_event):
    print("Press any key to stop...")
    if platform.system() == 'Windows':
        msvcrt.getch()
    else:
        input()
    stop_event.set()

def main():
    config_file = 'config.json'
    config = load_config(config_file)
    
    devices = config.get('devices', [])
    ping_count = config.get('ping_count', 4)
    timeout = config.get('timeout', 1)
    
    if not devices:
        print("No devices to ping found in configuration.")
        sys.exit(1)
    
    system = platform.system()
    if system not in ['Windows', 'Linux', 'Darwin']:
        raise ValueError(f"Unsupported operating system: {system}")

    current_time = datetime.now().strftime("%Y-%m-%d_%H.%M")
    log_file = os.path.join(os.getcwd(), f"ping_log_{current_time}.txt")
    open(log_file, 'w').close()

    results = {device: {'transmitted': 0, 'received': 0} for device in devices}

    stop_event = threading.Event()

    start_time = datetime.now()

    # Start the thread for key press detection
    key_thread = threading.Thread(target=wait_for_key_press, args=(stop_event,))
    key_thread.start()

    # Start the pinging thread
    ping_thread = threading.Thread(target=ping_devices_continuously, args=(devices, ping_count, timeout, results, stop_event, system))
    ping_thread.start()

    try:
        key_thread.join()
    except KeyboardInterrupt:
        print("Interrupted!")
    finally:
        stop_event.set()
        ping_thread.join()
        end_time = datetime.now()
        write_summary_to_log(log_file, results, start_time, end_time)
        print(f"Summary written to {log_file}")

if __name__ == '__main__':
    main()
