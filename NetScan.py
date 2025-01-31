import socket
import asyncio
import argparse
import ipaddress
import re
import random
import time
from colorama import Fore, Style, init


# Initialize colorama
init()

# Default maximum concurrent connections
DEFAULT_MAX_CONCURRENT_CONNECTIONS = 1000


# Function to resolve host
def resolve_host(host):
    try:
        if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", host):  # Direct IP
            return [host]
        elif '/' in host:  # CIDR notation (e.g., 192.168.1.0/24)
            return [str(ip) for ip in ipaddress.IPv4Network(host, strict=False)]
        else:  # Hostname or URL
            return [socket.gethostbyname(host)]
    except socket.gaierror:
        raise ValueError("Invalid host or domain name")


# Function to parse ports
def parse_ports(port_input):
    if port_input == "-":  # Scan all ports
        return range(1, 65536)
    elif "-" in port_input:  # Range of ports
        start, end = map(int, port_input.split("-"))
        return range(start, end + 1)
    else:  # Single or multiple ports
        return list(map(int, port_input.split(",")))


# Function to read IPs from a file
def read_ips_from_file(file_path):
    ips = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", line):  # Validate IP address format
                    ips.append(line)
                elif re.match(r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$", line):  # Validate domain name
                    ips.append(socket.gethostbyname(line))
        return ips
    except FileNotFoundError:
        raise ValueError(f"File {file_path} not found.")
    except Exception as e:
        raise ValueError(f"Error reading file {file_path}: {e}")

# Function to remove ANSI escape codes (colors)
def remove_ansi_escape_codes(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


# Function to scan a single port
async def scan_port(ip, port, semaphore, output_file):
    async with semaphore:
        await asyncio.sleep(random.uniform(0.01, 0.05))  # Introduce slight delay to avoid overwhelming the network
        conn = asyncio.open_connection(ip, port)
        try:
            reader, writer = await asyncio.wait_for(conn, timeout=0.5)  # Increased timeout for better accuracy
            writer.close()
            await writer.wait_closed()
            result = f"{Fore.GREEN}[+] {ip}:{port} is open{Style.RESET_ALL}"
            print(result)
            if output_file:
                # Remove color codes before writing to the file
                output_file.write(remove_ansi_escape_codes(result) + '\n')
        except (asyncio.TimeoutError, ConnectionRefusedError):
            pass  # Ignore closed ports
        except Exception as e:
            if "[WinError 5]" not in str(e):  # Filter out access denied errors
                result = f"{Fore.YELLOW}[!] Error scanning {ip}:{port}: {e}{Style.RESET_ALL}"
                print(result)
                if output_file:
                    # Remove color codes before writing to the file
                    output_file.write(remove_ansi_escape_codes(result) + '\n')


# Function to run async scanning
async def async_scan(ips, ports, max_connections, output_file):
    semaphore = asyncio.Semaphore(max_connections)
    tasks = [scan_port(ip, port, semaphore, output_file) for ip in ips for port in ports]
    await asyncio.gather(*tasks)


# Main function
def main():
    start_time = time.time()  # Time when scanning starts

    parser = argparse.ArgumentParser(description="High-speed masscan-like port scanner")
    parser.add_argument("host", type=str, nargs='?', default=None,
                        help="Host, IP range, or CIDR to scan. Ignored if -input is provided")
    parser.add_argument("-p", "--ports", type=str, default="1-1000",
                        help="Ports to scan (e.g., 80,443 or 1-1000 or all with '-')")
    parser.add_argument("-t", "--threads", type=int, default=DEFAULT_MAX_CONCURRENT_CONNECTIONS,
                        help="Maximum number of concurrent connections (default is 1000)")
    parser.add_argument("-i", "--input", type=str, help="File with IP addresses or domains to scan")
    parser.add_argument("-o", "--output", type=str, help="Output file to save scan results")

    args = parser.parse_args()

    try:
        # Check if input file is provided, otherwise use host
        if args.input:
            ips = read_ips_from_file(args.input)
        elif args.host:
            ips = resolve_host(args.host)
        else:
            raise ValueError("You must provide either a host or an input file.")

        ports = parse_ports(args.ports)

        # Prepare output file if needed
        output_file = None
        if args.output:
            output_file = open(args.output, 'w')

        print(f"{Fore.BLUE}Starting scan on {', '.join(ips)} ({len(ips)} IPs), ports: {args.ports}{Style.RESET_ALL}")

        # Print the selected IPs and ports
        for ip in ips:
            print(f"{Fore.CYAN}IP Address: {ip}{Style.RESET_ALL}")

        # Run the async scan with the user-specified number of concurrent connections
        asyncio.run(async_scan(ips, ports, args.threads, output_file))

        # Close the output file if opened
        if output_file:
            output_file.close()

    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")

    # Calculate and display the time taken for the scan
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"\n{Fore.YELLOW}Scan completed in {int(minutes)} minutes and {int(seconds)} seconds{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
