```markdown
# Ping Devices

This script continuously pings a list of devices and logs the results.

## Requirements

- Python 3.6 or higher
- Works on Windows, Linux, and macOS

## Setup

1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/ping_devices.git
   cd ping_devices
   ```

2. Create a virtual environment (optional but recommended):
   ```sh
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. Create a `config.json` file in the root directory of the repository with the following content:
   ```json
   {
       "devices": [
           "10.0.0.1",
           "10.0.0.2",
           "10.0.0.3",
           "10.0.0.4",
           "10.0.0.5",
           "10.0.0.6",
           "10.0.0.7"
       ],
       "ping_count": 4,
       "timeout": 2,
       "log_file": "ping_log.txt"
   }
   ```

## Usage

1. Run the script:
   ```sh
   python ping_devices.py
   ```

2. The script will continuously ping the devices listed in `config.json` and log the results to `ping_log.txt`.

3. To stop the script, press any key.

## Configuration

- **devices**: List of device IPs or hostnames to ping.
- **ping_count**: Number of ping attempts per device in each cycle.
- **timeout**: Timeout in seconds for each ping attempt.
- **log_file**: Path to the log file where results will be stored.

## Log File

The log file will be created in the current working directory with a timestamp in the filename (e.g., `ping_log_2023-05-16_12.00.txt`). It will contain a summary of the ping results for each device.

## Example

After running the script, a log file named `ping_log_<timestamp>.txt` will be created in the directory. The summary will include:

- Start Time
- End Time
- For each device: packets sent, packets received, and percentage of packets lost.

## Contributing

Feel free to submit issues or pull requests if you find any bugs or have suggestions for improvements.

## License

This project is licensed under the MIT License.
```