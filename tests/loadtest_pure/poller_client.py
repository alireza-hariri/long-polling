import argparse
import requests
import random
import uuid
import time


def random_in(a, b):
    return a + random.random() * (b - a)


def poller_client(
    endpoint: str,
    total_messages: int,
    user: int,
    check_first_id = True,
    delay_range=(0, 0.05),
    no_delay_prob=0.2,
) -> bool:
    """
    continually polls the server
    there is a random delay between each polling
    """
    last_id = 0
    all_ok = True
    # a random number as session (consistent for all requests of this client)
    session = uuid.uuid4().hex[:10]
    for _ in range(total_messages):
        if random.random() > no_delay_prob:
            time.sleep(random_in(*delay_range))
            
        resp = requests.get(endpoint, params={"session_id": session, "user_id": user})
        if resp.status_code == 200:
            data = resp.json()
            if check_first_id or last_id:
                if data["message"]["id"] == last_id + 1:
                    print(".", end="", flush=True)
                else:
                    all_ok = False
                    print(f"bad seq_id last={last_id} message={data['message']}")
            last_id = data["message"]['id']
            assert data["message"]['user'] == user
        elif resp.status_code == 204:
            print("no content!")
        else:
            all_ok = False
            print(resp)

    
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Main program")
    parser.add_argument(
        "-e", "--endpoint", type=str, required=True, help="Endpoint URL"
    )
    parser.add_argument(
        "-t",
        "--total-messages",
        type=int,
        required=True,
        help="Total number of messages",
    )
    parser.add_argument(
        "-r",
        "--delay-range",
        type=float,
        nargs=2,
        default=[0, 0.2],
        help="Delay range (min, max) in seconds",
    )
    parser.add_argument(
        "-u",
        "--user",
        type=int,
        help="username or user_id",
    )

    args = parser.parse_args()
    poller_client(
        endpoint=args.endpoint,
        total_messages=args.total_messages,
        user=args.user,
        delay_range=tuple(args.delay_range),
    )

"""
python ./tests/poller_client.py -e http://127.0.0.1:8000/long-polling -t 100 -r 0 0.1
"""
