import random
import argparse
import time
from tests.loadtest_pure.poller_client import poller_client
from multiprocessing.pool import ThreadPool

def random_in(a, b):
    return a + random.random() * (b - a)


def user_sessions_test(
    total_messages: int,
    user: int,
    n_session=2,
    initialization_delay=(0,0.1),
    max_delays=[0.0, 0.1, 0.15],
):
    time.sleep(random_in(*initialization_delay))
    pool = ThreadPool(processes=n_session)
    results = []

    for n in range(n_session):
        m_delay = random_in(0, max_delays[n])
        results.append(
            pool.apply_async(
                poller_client,
                args=(
                    "http://127.0.0.1:8000/long-polling",
                    total_messages,
                    user,
                    True,
                    (0, m_delay),
                ),
            )
        )

    all_ok = True
    for n,res in enumerate(results):
        r = res.get()
        if r == True:
            print(f"\nsession-{n} user-{user} .. ok")
        else:
            print(f"\nsession-{n} user-{user} .. Failed !!!")
            all_ok = False
            print(r)
            print("!!!!!")
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="User Sessions")
    parser.add_argument(
        "-t",
        "--total-messages",
        type=int,
        required=True,
        help="Total number of messages",
    )
    parser.add_argument(
        "-u",
        "--user",
        type=int,
        required=True,
        help="User ID",
    )
    parser.add_argument(
        "-n",
        "--n-session",
        type=int,
        default=2,
        help="Number of sessions (default: 2)",
    )
    parser.add_argument(
        "--max-delays",
        type=float,
        nargs="+",
        default=[0.01, 0.1, 0.2],
        help="Maximum delays (default: [0.01, 0.1])",
    )

    args = parser.parse_args()
    
    user_sessions(
        total_messages=args.total_messages,
        user=args.user,
        max_initialization_delay=args.max_initialization_delay,
        n_session=args.n_session,
        max_delays=args.max_delays,
    )