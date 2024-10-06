from tests.loadtest_pure.poller_client import poller_client
import argparse
import random
import gevent
import time

def random_in(a, b):
    return a + random.random() * (b - a)


def user_sessions_test(
    total_messages: int,
    user: int,
    n_session=2,
    initialization_delay=(0,0.1),
    max_delays=[0.0, 0.1, 0.15],
):
    tasks : List[gevent.Greenlet] = []
    host = "http://127.0.0.1:8000"
    gevent.sleep(random_in(*initialization_delay))


    for n in range(n_session):
        m_delay = random_in(0, max_delays[n])
        tasks.append(
            gevent.spawn(
                poller_client,
                host + "/long-polling",
                total_messages,
                user,
                True,
                (0, m_delay),
            )
        )

    all_ok = True
    for n,t in enumerate(tasks):
        r = t.get()
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