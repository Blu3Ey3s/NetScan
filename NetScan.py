import socket
import asyncio
import argparse
import ipaddress
import re
import aiofiles
from colorama import Fore, Style, init
import time
# Initialize colorama
init(autoreset=True)

LOGO = fr"""{Fore.GREEN}
                              ____   _____  _________
                          ( (    /|(  ____ \\__   __/
                          |  \  ( || (    \/   ) (   
                          |   \ | || (__       | |   
                          | (\ \) ||  __)      | |   
                          | | \   || (         | |   
                          | )  \  || (____/\   | |   
                          |/    )_)(_______/   )_(   
                                                     
         _______  _______  _______  _        _        _______  _______ 
        (  ____ \(  ____ \(  ___  )( (    /|( (    /|(  ____ \(  ____ )
        | (    \/| (    \/| (   ) ||  \  ( ||  \  ( || (    \/| (    )|
        | (_____ | |      | (___) ||   \ | ||   \ | || (__    | (____)|
        (_____  )| |      |  ___  || (\ \) || (\ \) ||  __)   |     __)
              ) || |      | (   ) || | \   || | \   || (      | (\ (   
        /\____) || (____/\| )   ( || )  \  || )  \  || (____/\| ) \ \__
        \_______)(_______/|/     \||/    )_)|/    )_)(_______/|/   \__/                                           
{Style.RESET_ALL}"""
# Default maximum concurrent connections
DEFAULT_MAX_CONCURRENT_CONNECTIONS = 1000

def resolve_host(host):
    """Преобразует доменное имя или IP-адрес в список IP-адресов."""
    try:
        if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", host):
            return [host]  # Уже IP
        elif '/' in host:
            return [str(ip) for ip in ipaddress.IPv4Network(host, strict=False)]
        else:
            return [socket.gethostbyname(host)]  # Преобразуем домен в IP
    except (socket.gaierror, ValueError):
        raise ValueError(f"Invalid host or domain name: {host}")



def parse_ports(port_input):
    """Разбирает строку с портами (одиночные, диапазон или все)."""
    try:
        if port_input == "-":
            return range(1, 65536)  # Все порты
        elif "-" in port_input:
            start, end = map(int, port_input.split("-"))
            if 1 <= start <= end <= 65535:
                return range(start, end + 1)
        else:
            ports = list(map(int, port_input.split(",")))
            if all(1 <= p <= 65535 for p in ports):
                return ports
        raise ValueError("Invalid port range")
    except ValueError:
        raise ValueError(f"Invalid port input: {port_input}")



def remove_ansi_escape_codes(text):
    """Удаляет ANSI коды из текста."""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


async def scan_port(ip, port, semaphore, output_file):
    """Сканирует указанный порт асинхронно с учетом таймаута."""
    async with semaphore:
        try:
            conn = asyncio.open_connection(ip, port)
            reader, writer = await asyncio.wait_for(conn, timeout=1.0)  # Увеличен таймаут до 1 сек
            result = f"{Fore.GREEN}[+] {ip}:{port} is open{Style.RESET_ALL}"
            writer.close()
            await writer.wait_closed()
        except (asyncio.TimeoutError, ConnectionRefusedError):
            return  # Порт закрыт или недоступен
        except OSError as e:
            if e.winerror == 121:  # Превышен таймаут семафора
                return
            result = f"{Fore.YELLOW}[!] Error scanning {ip}:{port}: {e}{Style.RESET_ALL}"
        except Exception as e:
            result = f"{Fore.YELLOW}[!] Unexpected error scanning {ip}:{port}: {e}{Style.RESET_ALL}"
        else:
            result = None

        if result:
            print(result)
            if output_file:
                async with aiofiles.open(output_file, 'a') as f:
                    await f.write(remove_ansi_escape_codes(result) + '\n')


async def async_scan(ips, ports, max_connections, output_file):
    """Асинхронно сканирует список IP-адресов и портов."""
    semaphore = asyncio.Semaphore(max_connections)
    tasks = [asyncio.create_task(scan_port(ip, port, semaphore, output_file)) for ip in ips for port in ports]
    await asyncio.gather(*tasks)



def main():
    print(LOGO)
    start_time = time.time()

    parser = argparse.ArgumentParser(description="High-speed port scanner like a Masscan written in Python PL")
    parser.add_argument("host", type=str, nargs='?', default=None, help="Host(domain/URL), IP range, or CIDR to scan.")
    parser.add_argument("-p", "--ports", type=str, default="1-1000", help="Ports to scan (e.g., 80,443 or 1-1000 or '-')")
    parser.add_argument("-t", "--threads", type=int, default=DEFAULT_MAX_CONCURRENT_CONNECTIONS, help="Max concurrent connections(default value == 1000)")
    parser.add_argument("-o", "--output", type=str, help="Output file to save scan results(output file == simple txt file like a result.txt")

    args = parser.parse_args()

    try:
        if args.host:
            ips = resolve_host(args.host)
        else:
            raise ValueError("You must provide a host.")

        ports = parse_ports(args.ports)
        output_file = open(args.output, 'w') if args.output else None

        print(f"{Fore.BLUE}Starting scan on {args.host}, ports: {args.ports}{Style.RESET_ALL}")
        asyncio.run(async_scan(ips, ports, args.threads, output_file))
        if output_file:
            output_file.close()
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"\n{Fore.YELLOW}Scan completed in {int(minutes)} minutes and {int(seconds)} seconds{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
