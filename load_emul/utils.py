import logging
import os
import setproctitle
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

def do_something(pname:str, sleep:int, work:int):
    """ Function emulating a process activity

    Args:
        pname (str): process name visible in top command
        sleep (int): pause time (s) before generating cpu load
        work (int): duration (s) of the cpu load
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(process)d] %(message)s",
        force=True   # ensure it overrides forked empty config
    )
    setproctitle.setproctitle(f'{pname}')
    pid = os.getpid()
    logging.info(f'process {pid}. sleep for {sleep}s')
    time.sleep(sleep)
    logging.info(f'process {pid}. work for {work}s')
    start_time = time.time()
    while time.time() - start_time < work:
        _ = 1234567 * 7654321 / 1.000000001
    logging.info(f'process {pid}. done')