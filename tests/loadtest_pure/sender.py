from geventhttpclient import Session
import argparse
import random
import gevent
import time


def random_in(a, b):
    return a + random.random() * (b - a)


def sender(
    user: int,
    req_per_sec: float,
    N: int,
    initialization_delay=(0, 0.5),
):
    gevent.sleep(random_in(*initialization_delay))
    s = Session()
    t0 = time.time()
    host = "http://127.0.0.1:8000"

    for n in range(N):
        s.get(
            url=host + "/send-hello",
            params={
                "user_id": user,
                "seq_id": n + 1,
            },
        )
        t = time.time()
        if (t - t0) < n / req_per_sec:
            gevent.sleep(n / req_per_sec - (t - t0))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sender function arguments")
    parser.add_argument("-u", "--user", type=int, help="User ID")
    parser.add_argument(
        "-r",
        "--req_per_sec",
        type=float,
        default=3,
        help="Requests per second",
    )
    parser.add_argument(
        "-N",
        type=int,
        default=20,
        help="Requests per second",
    )
    args = parser.parse_args()
    # Convert the Namespace object to a dictionary and unpack it into keyword arguments
    sender(**vars(args))
