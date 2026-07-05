import random
import argparse

def generate_fake_line():
    # Generates one full line of fake log data
    timestamp = f"{random.randint(2020, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d} {random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
    ip_address = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    method = random.choice(["GET", "POST", "PUT", "DELETE"])
    url = f"/api/v1/resource/{random.randint(1, 100)}"
    protocol = random.choice(["HTTP/1.0", "HTTP/1.1", "HTTP/2"])
    status_code = random.choice([200, 201, 400, 401, 403, 404, 500, 502, 503])
    size = random.randint(0, 5000)
    if size == 0:
        size = "-"
    return f"{timestamp} {ip_address} \"{method} {url} {protocol}\" {status_code} {size}"

def write_log_file(num_lines):
    # Writes a specified number of fake log lines to a file
    with open("static/fake_logs.txt", "w") as log_file:
        for _ in range(num_lines):
            log_line = generate_fake_line()
            log_file.write(log_line + "\n")
            
def parse_args():
    parser = argparse.ArgumentParser(description="Generates a fake logfile with specified line count")
    parser.add_argument("--count", type=int, default=50000, help="number of lines in the file, default 50000")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    write_log_file(args.count)
    print(f"{args.count} lines generated in static/fake_logs.txt")