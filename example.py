from fastapi import FastAPI, Response, HTTPException
from asyncio import TimeoutError
from longPoll import LongPollable


USER_ID = "10"

app = FastAPI()

lp = LongPollable()
hello = lp.create_message_type("hello", int)

hello.sequentse_id = 1


@app.get("/send-hello")
async def send_hello(user_id: str ):

    send_ok = await hello.send_message(
        user=USER_ID,                # any hashable object
        message=hello.sequentse_id,  # type checked message type !
    )
    hello.sequentse_id += 1
    return {"sent": send_ok}


@app.get("/long-polling")
async def long_polling(session_id: str, user_id: str):
    # write your login logic here
    # ...
    #
    try:
        # waiting 10 seconds for new messages sent to this user
        message = await lp.wait_for_message(
            user=user_id,   # any hashable obj representing reciver 
            session=session_id,  # any hashable obj representing the session 
            timeout=10,
        )
        return message
    except TimeoutError:
        raise HTTPException(
            status_code=204,  # 408 is also a resanable response code if the client
            detail="No content",
        )
