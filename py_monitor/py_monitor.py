import psutil
import time
import csv
import os
import logging
import sys

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# configuration 
interval_seconds = 5

def initialize_csv(target_csv:str):
    """
       Create .csv file with header if not exist
    Args:
        target_csv (str): .csv file storing the metrics captured
    """    
    if not os.path.exists(target_csv):
        with open(target_csv, mode='w', newline='') as f:
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
        logging.info(f"output file {target_csv} created")
    else:
        raise FileExistsError
    

def collect_and_store(output_csv:str='output.csv'):
    """
       Scan process information throught psutil to gather metrics
       Write values in .csv file

    Args:
        output_csv (str, optional): csv file storing the metrics captured. Defaults to 'output.csv'.
    """
    try:
        initialize_csv(output_csv)
    except FileExistsError:
        logging.exception(f"{output_csv} already exists. Cannot overwrite")
        sys.exit(1)

    logging.info("starting monitoring ...")
    try:
        while True:
            scan_start = time.time()
            batch_data = []
            attrs = [
                'pid',
                'name',
                'status',
                'cpu_percent',
                'memory_info',
                'num_threads'
            ]

            for proc in psutil.process_iter(attrs):
                try:
                    # 'oneshot' context manager creates a snapshot of the process
                    # it's faster/safer to read inside this block
                    with proc.oneshot():
                        logging.debug(f"analyzing pid {proc.pid}")
                        row = [
                            scan_start,  # epoch time
                            proc.pid,
                            proc.name(),
                            proc.status(),
                            proc.cpu_percent(),  # CPU usage since last call
                            proc.memory_info().rss / 1024 / 1024,  # get memory in Mb
                            proc.num_threads()
                        ]
                        batch_data.append(row)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # process died or is locked during iteration, skip it
                    continue
                
            if batch_data:
                with open(output_csv, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(batch_data)
                
            # compute time duration the substract to initial sleep time to prevent shifting measures
            scan_duration = time.time() - scan_start
            sleep_time = max(0, interval_seconds - scan_duration)
            logging.debug(f"scan took {scan_duration:.2f}s. Sleeping {sleep_time:.2f}")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logging.info("Stop monitoring")


if __name__ == "__main__":
    collect_and_store()