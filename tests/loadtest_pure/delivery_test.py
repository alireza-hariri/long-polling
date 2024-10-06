# when a user have multiple consumer clients, the delivery can get tricky
# so this is the main this that we test here

from tests.loadtest_pure.user_sessions import user_sessions_test
from tests.loadtest_pure.sender import sender
from joblib import Parallel, delayed
import threading
import argparse
import random

n_message = 20


def a_user(user: int, rps: float):
    t = threading.Thread(
        target=sender,
        args=(
            user,
            rps,
            n_message,
            (0.1, 1),  # (2.7, 3.8),
        ),
    )
    t.start()
    return user_sessions_test(
        n_message,
        user,
        n_session=random.choice([1,1,2,3]), # most of users only have one sessions
        initialization_delay=(0, 0.2),
    )


def simulate_n_users(n_user, uid_bias):
    " single process with n users (in n threads) "
    reults = Parallel(n_jobs=n_user, backend="threading")(
        delayed(a_user)(uid_bias + n + 1, rps=random.choice(range(5, 25)))
        for n in range(n_user)
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
    simulate_n_users(**vars(args))
   
