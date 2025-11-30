import multiprocessing
import time
from random import randint
import os
import setproctitle
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

class LoadGenerator:
    """ Class to emulate load on machine by spawning subprocesses
    """
    def __init__(self):
        """ Constructor
        """        
        self.max_pause = 10
        self.max_work = 30
        self.max_iteration = 3
        self.min_process = 3
        self.max_process = 6


    def __do_something__(self, pname:str, sleep:int, work:int):
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
        while (time.time() - start_time < work):
            _ = 1234567 * 7654321 / 1.000000001
        logging.info(f'process {pid}. done')


    def generate_load(self):
        """ Function spawning a set of subprocesses
        """        
        processes = []
        for i in range(1, randint(self.min_process, self.max_process)):
            process_name = f'{self.__class__.__name__}_{i}'
            sleep_time = randint(1, self.max_pause)
            cpu_load_time = randint(5, self.max_work)
            p =multiprocessing.Process(target=self.__do_something__, args=(process_name, sleep_time, cpu_load_time))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()


if __name__ == "__main__":
    my_load = LoadGenerator()
    my_load.generate_load()