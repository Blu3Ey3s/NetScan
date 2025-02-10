# NetScan
(***High-Speed Port Scanner***)

This is a high-speed port scanner written in Python, designed to quickly scan IP addresses and port
ranges.<br>It leverages asynchronous programming to perform multiple port scans concurrently, similar
to the
functionality provided by tools like Masscan.<br>The script supports custom input for the host, port
ranges, and the number of concurrent connections.
Features

Supports scanning for a single IP address, domain names, or IP ranges (CIDR).
Allows for scanning of a range of ports or specific ports.
Customizable number of concurrent connections (threads) to control scan speed.
Option to save the results to a file.
Easy-to-use command-line interface with detailed help.

# Installation

Clone the repository or download the script file.
Install necessary dependencies:
<br>Run this script in the virtualenv(venv).<br>
### Download the virtual environment:
    python -m venv venv
### Activate the virtual environment:
    
    source ./venv/bin/activate
### Install Dependency packages:
    pip install -r requirements.txt
    
# Examples of use

### Scan the first 1000 ports of a single host:

    python NetScan.py example.com


### Scan specific ports (e.g., 80, 443, and 8080) on a host:

    python scanner.py example.com -p 80,443,8080

### Scan a specific range of ports (e.g., ports 1 to 1000):

    python scanner.py example.com -p 1-1000


### Scan an IP range or CIDR block:

    python scanner.py 192.168.1.0/24 -p 22-80

### Scan with a customized number of concurrent connections (default is 300):

    python scanner.py example.com -p 1-1000 -t 500


### Save the scan results to a file (result.txt):

    python scanner.py example.com -p 1-1000 -o result.txt

### Example Output

The output of the script will show open ports in green, with a message indicating the IP address and port. For example:

    [+] example.com:80 is open
    [+] example.com:443 is open

If a file is specified using the -o option, the results will also be written to the file in plain text.

# Main Arguments

    host (optional): The host (IP address, domain name, or CIDR block) to scan.
    -p, --ports: Specify the ports to scan (e.g., 80,443, 1-1000, or - for all ports).
    -t, --threads: Set the number of concurrent connections (default is 300).
    -o, --output: Output file to save scan results.

### Example Command

    python scanner.py 192.168.1.0/24 -p 1-1024 -t 500 -o results.txt

# License

This script is open-source and licensed under the MIT License. Feel free to modify and use it for your personal or commercial projects.