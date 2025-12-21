import multiprocessing
from random import randint
import logging
from utils import do_something

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

class LoadGenerator:
    """ Class to emulate load on machine by spawning subprocesses
    """
    def __init__(self, max_pause:int=10, max_work:int=30, max_iter:int=3, min_procs:int=3, max_procs:int=6):
        """ Constructor
        """        
        self.max_pause = max_pause
        self.max_work = max_work
        self.max_iteration = max_iter
        self.min_process = min_procs
        self.max_process = max_procs

    def generate_load(self):
        """ Function spawning a set of subprocesses
        """        
        processes = []
        for i in range(1, randint(self.min_process, self.max_process)):
            process_name = f'{self.__class__.__name__}_{i}'
            sleep_time = randint(1, self.max_pause)
            cpu_load_time = randint(5, self.max_work)
            p =multiprocessing.Process(target=do_something, args=(process_name, sleep_time, cpu_load_time))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()


if __name__ == "__main__":
    my_load = LoadGenerator()
    my_load.generate_load()