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
        """
        logging.info("starting monitoring ...")
        host_cores = psutil.cpu_count()
        try:
            while True:
                scan_start = time.time()
                batch_data = []
                current_pids = set()  # get list of current pids to see who is still alive

                for proc in psutil.process_iter():
                    pid = proc.pid
                    current_pids.add(pid)
                    if pid not in self.process_cache:
                        self.process_cache[pid] = proc
                        # call once to "set" the first measurement
                        self.process_cache[pid].cpu_percent()
                        continue

                    try:
                        # 'oneshot' context manager creates a snapshot of the process
                        # it's faster/safer to read inside this block
                        p = self.process_cache[pid]
                        with p.oneshot():
                            logging.debug(f"analyzing pid {p.pid}")
                            # divide by # of cores for global load
                            cpu = p.cpu_percent() / host_cores
                            row = [
                                scan_start,  # epoch time
                                p.pid,
                                p.name(),
                                p.status(),
                                cpu,  # CPU usage since last call
                                p.memory_info().rss / 1024 / 1024,  # get memory in Mb
                                p.num_threads()
                            ]
                            batch_data.append(row)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        # process died or is locked during iteration, skip it
                        continue

                self.process_cache = {pid: obj for pid, obj in self.process_cache.items()
                                      if pid in current_pids}
                if batch_data:
                    with open(self.target_csv, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerows(batch_data)

                # compute time duration the subtract to initial sleep time to prevent shifting measures
                scan_duration = time.time() - scan_start
                sleep_time = self.interval_seconds
                logging.debug(f"scan took {scan_duration:.2f}s. Sleeping {sleep_time:.2f}")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logging.info("Stop monitoring")


if __name__ == "__main__":
     try:
         logging.info("START OF TEST")
         fake_load = subprocess.Popen([sys.executable, "-m", "load_emul.generator"])
         my_monitor = ProcsCollect()
         my_monitor.collect_and_store()
         fake_load.wait()
         logging.info("END OF TEST")
     except FileExistsError as e:
         logging.exception(f"Output file already exists.\n{e}")