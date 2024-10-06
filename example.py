from fastapi import FastAPI, Response, HTTPException
from asyncio import TimeoutError
from pydantic import BaseModel
from longPoll import LongPollable


class ExampleDTO(BaseModel):
    id: int
    user: int

app = FastAPI()

lp = LongPollable()
hello = lp.create_message_type(
    event_name="hello",
    schema=ExampleDTO
)


@app.get("/send-hello")
async def send_hello(user_id: int,seq_id:int):

    # type checked message !
    send_ok = await hello.send_message(
        user=user_id,                # any hashable object
        message=ExampleDTO(
            id = seq_id,  
            user=user_id
        )
    )
    return {"sent": send_ok}


@app.get("/long-polling")
async def long_polling(session_id: str, user_id: int):
    # write your login logic here
    # ...
    #
    try:
        # waiting 10 seconds for new messages sent to this user
        message = await lp.wait_for_message(
            user=user_id,   # any hashable obj representing receiver 
            session=session_id,  # any hashable obj representing the session 
            timeout=10,
        )
        return message
    except TimeoutError:
        raise HTTPException(
            status_code=204,  # 408 is also a reasonable response code if the client
            detail="No content",
        )
