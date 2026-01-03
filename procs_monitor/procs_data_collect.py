import csv
from  datetime import datetime as dt
import logging
import os
import psutil
from socket import gethostname
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProcsCollect:
    def __init__(
            self,
            output_csv:str=f'/tmp/py_monitor_data_{gethostname()}_{dt.now().strftime("%Y%m%d_%H%M%S")}.csv',
            interval_s:float=5):
        """
        Constructor

        Args:
            output_csv: path to store csv file with data collected
            interval_s: frequency of monitoring
        """
        self.target_csv = output_csv
        self.interval_seconds = float(interval_s)
        self.process_cache = {}
        if not os.path.exists(self.target_csv):
            with open(self.target_csv, mode='w', newline='') as f:
                writer = csv.writer(f)
                # define file header
                writer.writerow([
                    'epoch_timestamp',
                    'pid',
                    'name',
                    'status',
                    'cpu_percent',
                    'memory_rss_mb',
                    'num_threads'
                ])
            logging.info(f"output file {self.target_csv} created")
        else:
            raise FileExistsError

    def collect_and_store(self):
        """
         scan process information with psutil to gather metrics
         write values in .csv file

        Returns:

        """
        logging.info("Starting monitoring...")
        # host_cores = psutil.cpu_count()  # divide cpu+percent per host_cores if you want overall cpu usage
        # Pre-define the attributes to fetch in bulk
        attrs = ['pid', 'name', 'status', 'memory_info', 'num_threads']
        next_scan_time = time.time()

        try:
            # Keep the file open to avoid the overhead of repeated open/close
            with open(self.target_csv, mode='a', newline='') as f:
                writer = csv.writer(f)

                while True:
                    scan_start = time.time()
                    batch_data = []
                    active_pids = set()

                    # 1. Use process_iter with 'attrs' for massive speedup
                    try:
                        for proc in psutil.process_iter(attrs=attrs, ad_value=None):
                            # If access denied, proc.info will contain None values
                            if proc.info['pid'] is None:
                                continue  # Skip inaccessible processes gracefully

                            pid = proc.info['pid']
                            active_pids.add(pid)

                            try:
                                # 2. Manage CPU state tracking
                                if pid not in self.process_cache:
                                    self.process_cache[pid] = proc
                                    proc.cpu_percent()  # Initialize first call
                                    cpu_val = 0.0
                                else:
                                    self.process_cache[pid] = proc
                                    cpu_val = proc.cpu_percent()

                                # 3. Access data from proc.info (filled by process_iter)
                                row = [
                                    scan_start,
                                    pid,
                                    proc.info['name'],
                                    proc.info['status'],
                                    cpu_val,
                                    proc.info['memory_info'].rss / (1024 * 1024),
                                    proc.info['num_threads']
                                ]
                                batch_data.append(row)

                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except (psutil.Error, OSError) as e1:
                        # Catch catastrophic failures in process iteration itself
                        logging.warning(f"Process iteration error: {e1}")

                    # 4. Clean cache: remove PIDs that no longer exist
                    self.process_cache = {pid: p for pid, p in self.process_cache.items()
                                          if pid in active_pids}

                    # 5. Bulk write
                    if batch_data:
                        writer.writerows(batch_data)
                        f.flush()  # Ensure data is written to disk

                    # 6. Prevent "Time Drift"
                    next_scan_time += self.interval_seconds
                    current_time = time.time()
                    sleep_time = max(0.0, next_scan_time - current_time)
                    # Log if we're falling behind
                    if sleep_time == 0.0:
                        behind = current_time - next_scan_time
                        logging.warning(f"Scan took too long! Behind by {behind:.2f}s")

                    logging.debug(f"Sleeping {sleep_time:.2f}s until next scan")
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logging.info("Stop monitoring")


if __name__ == "__main__":
     try:
         min_p = 4
         max_p = 8
         logging.info("START OF TEST")
         fake_load = subprocess.Popen([
             sys.executable,
             "-m", "load_emul.generator",
             "--min_procs", str(min_p),
             "--max_procs", str(max_p)
         ])
         my_monitor = ProcsCollect()
         my_monitor.collect_and_store()
         fake_load.wait()
         logging.info("END OF TEST")
     except FileExistsError as e:
         logging.exception(f"Output file already exists.\n{e}")