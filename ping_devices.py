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
    import select

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def parse_ping_output(output, system):
    """ Parse the ping output to extract the packet loss summary """
    transmitted, received, loss = 0, 0, 0
    if system == 'Windows':
        for line in output.split('\n'):
            if 'Packets: Sent =' in line:
                parts = line.split(',')
                transmitted = int(parts[0].split('=')[1].strip())
                received = int(parts[1].split('=')[1].strip())
                loss_str = parts[2].split('=')[1].strip()
                loss = int(loss_str.split()[0])  # Extract the numeric part before "(loss)"
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
    output = result.stdout.decode()

    # Extract summary information
    transmitted, received, loss = parse_ping_output(output, system)

    return transmitted, received

def ping_devices_continuously(devices, ping_count, timeout, results, stop_event, system):
    while not stop_event.is_set():
        for device in devices:
            transmitted, received = ping_device(device, ping_count, timeout, system)
            results[device]['transmitted'] += transmitted
            results[device]['received'] += received
        time.sleep(1)  # Add a small delay to avoid overwhelming the network

def write_summary_to_log(log_file, results):
    with open(log_file, 'a') as log:
        log.write("\nSummary:\n")
        for device, stats in results.items():
            transmitted = stats['transmitted']
            received = stats['received']
            lost = transmitted - received
            loss_percentage = (lost / transmitted) * 100 if transmitted > 0 else 100.0
            log.write(f"Device: {device}\n")
            log.write(f"Packets: Transmitted = {transmitted}, Received = {received}, Lost = {loss_percentage:.1f}%\n")
            log.write("\n")

def wait_for_key_press(stop_event):
    system = platform.system()
    print("Press any key to stop...")
    if system == 'Windows':
        msvcrt.getch()  # Wait for a key press on Windows
    else:
        input()  # Wait for Enter key press on Unix-like systems
    stop_event.set()

def main():
    config = load_config('config.json')
    devices = config['devices']
    ping_count = config['ping_count']
    timeout = config['timeout']

    # Determine the current operating system
    system = platform.system()
    if system not in ['Windows', 'Linux', 'Darwin']:  # Darwin is macOS
        raise ValueError(f"Unsupported operating system: {system}")

    # Create log file with current date and time
    current_time = datetime.now().strftime("%Y-%m-%d_%H.%M")
    log_file = os.path.join(os.getcwd(), f"ping_log_{current_time}.txt")

    # Ensure log file is empty at start
    open(log_file, 'w').close()

    # Initialize results dictionary
    results = {device: {'transmitted': 0, 'received': 0} for device in devices}

    stop_event = threading.Event()

    # Start the pinging in a separate thread
    ping_thread = threading.Thread(target=ping_devices_continuously, args=(devices, ping_count, timeout, results, stop_event, system))
    ping_thread.start()

    # Start a thread to listen for key press to stop
    key_thread = threading.Thread(target=wait_for_key_press, args=(stop_event,))
    key_thread.start()

    try:
        key_thread.join()  # Wait for the key press thread to finish
    except KeyboardInterrupt:
        print("Interrupted!")
    finally:
        stop_event.set()
        ping_thread.join()
        write_summary_to_log(log_file, results)
        print(f"Summary written to {log_file}")

if __name__ == '__main__':
    main()
