# when a user have multiple consumer clients, the delivery can get tricky
# so this is the main this that we test here

from tests.loadtest_pure.user_sessions import user_sessions_test
from tests.loadtest_pure.sender import sender
from joblib import Parallel, delayed
from geventhttpclient import get
import threading
import requests
import argparse
import gevent
import random
import math

n_message = 20


def a_user(user: int, rps: float) -> bool:
    # clear the message queue
    get("http://127.0.0.1:8000/clear-queue", params={"user_id": user}) # blocking!
    # make sender
    t_send = gevent.spawn(
        sender,
        user,
        rps,
        n_message,
        (0.1, 1),  # (2.7, 3.8),
    )
    # make reciver sessions
    return user_sessions_test(
        n_message,
        user,
        n_session=random.choice([1, 1, 2, 3]),  # most of users only have one sessions
        initialization_delay=(0, 0.2),
    )


def simulate_n_users_gevent(n_user, uid_bias):
    tasks = []
    for n in range(n_user):
        tasks.append(
            gevent.spawn(a_user, uid_bias + n + 1, rps=random.choice(range(5, 15)))
        )
    return all(t.get() for t in tasks)


def simulate_n_users_thread(n_user, uid_bias):
    N_THREAD = 2
    user_per_thread = math.ceil(n_user / N_THREAD)
    backend=  "threading"
    reults = Parallel(n_jobs=n_user, backend=backend)(
        delayed(simulate_n_users_gevent)(
            user_per_thread, uid_bias + n * user_per_thread
        )
        for n in range(N_THREAD)
    )
    assert all(reults)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--n-user",
        type=int,
        default=50,
        help="Number of users",
    )
    parser.add_argument(
        "-b",
        "--uid-bias",
        type=int,
        default=0,
    )
    args = parser.parse_args()
    simulate_n_users_gevent(**vars(args))
