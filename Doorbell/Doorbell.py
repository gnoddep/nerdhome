import threading
from time import sleep

class Doorbell(threading.Thread):
    def __init__(self, verbose=False):
        super(Doorbell, self).__init__()

        self._verbose = verbose
        self._running = True
        self._condition = threading.Condition(threading.Lock())
        self._ring_times = 0
        self._relay = None

    def run(self):
        with self._condition:
            while self._running:
                self._condition.wait()

                while self._ring_times > 0:
                    if self._verbose:
                        print('Ring!')

                    self._relay.on()
                    sleep(0.25)
                    self._relay.off()

                    self._ring_times -= 1

                    if self._ring_times > 0:
                        sleep(0.25)

                self._relay = None

    def stop(self):
        with self._condition:
            self._relay = None
            self._ring_times = 0
            self._running = False
            self._condition.notify()

        self.join()

    def ring(self, relay, times=1):
        if self._condition.acquire(blocking=False):
            try:
                if self._verbose:
                    print('Ringing', str(times), 'times')
                self._relay = relay
                self._ring_times = times
                self._condition.notify()
            finally:
                self._condition.release()
