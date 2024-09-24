import time


def wait_until(condition: callable, timeout: float):
    start_time = time.time()

    while not condition():
        if time.time() - start_time > timeout:
            return False

        time.sleep(0.01)

    return True
