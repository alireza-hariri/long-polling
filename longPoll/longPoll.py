import asyncio
import time
from collections import deque
from pydantic import BaseModel, Field, ConfigDict
from typing import TypeVar, Type, Generic, Any, Hashable, List, Dict, Set
from enum import Enum, auto

T = TypeVar("T")
UserType = TypeVar("User", bound=Hashable)
SessoinType = TypeVar("Session", bound=Hashable)

#TODO: add logging insted of this shit
DEBUG = True
def debug_msg(txt):
    if DEBUG: print(f"{txt}")

async def with_delay(coroutine, delay):
    await asyncio.sleep(delay)
    await coroutine


class TypeLessMessage(BaseModel):
    event_name: str
    message: Any


class EventType(Generic[T]):
    def __init__(self, name, poller):
        self.name = name
        self.poller = poller

    async def send_message(self, user: UserType, message: T) -> bool:
        await self.poller.send_message_no_type(user, message, self.name)
        return True


class UserState(Enum):
    """what the user is waiting for now ?"""

    # waiting for all connection to come
    pending = auto()
    # waiting for message
    waiting_for_message = auto()
    # sending
    sending = auto()


EPCILON_DELAY = 0.0001  # 0.1 ms
PENDING_DELAY_BIG = 3  # first connection to connection ready delay



class UserData(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    user_state: UserState
    # is message ready? set the consume_message before triggering this event
    msg_ready_event: asyncio.Event = Field(default_factory=lambda: asyncio.Event())
    # small delay after pending - keep new connections pending when first_consumption started
    con_ready_event: asyncio.Event = Field(default_factory=lambda: asyncio.Event())
    # unexpired messages sent to this user
    message_queue: deque[TypeLessMessage] = Field(default_factory=lambda: deque())
    # the message to be consumed immediately
    consume_message: TypeLessMessage | None = None
    # indecateds that last message is setted but not consumed
    # **just for debuggig** - all messages should be expired when this time is reached
    # expiration_time: float | None = None
    # # this shoud be triggerd at expiration_time (by asyncio) (will delete the object)
    # expiration_event: asyncio.Event = Field(default_factory=lambda: asyncio.Event())
    # TODO: expireation logic

    # number of consumptions for last message
    last_message_clients: Set[SessoinType] = Field(default_factory=set)
    # number of pending connections
    pending_clients: Set[SessoinType] = Field(default_factory=set)

    pending_end_task: asyncio.Task | None = None
    pending_end_time: float | None = None
    send_task: asyncio.Task | None = None

    def end_the_pending_after(self, delay):
        end = time.time() + delay
        if (self.pending_end_time is None) or (end < self.pending_end_time):
            self.pending_end_time = end
            if self.pending_end_task:
                self.pending_end_task.cancel()
            self.pending_end_task = asyncio.create_task(
                with_delay(pending_end(self), delay)
            )

    def got_connection(self, session_id: SessoinType):

        if self.user_state == UserState.pending:
            self.end_the_pending_after(PENDING_DELAY_BIG)
        else:
            debug_msg(f"got connection and state is {self.user_state}")

        self.pending_clients.add(session_id)
        if self.pending_clients == self.last_message_clients:
            if len(self.pending_clients) > 0:
                if self.user_state == UserState.pending:
                    self.end_the_pending_after(EPCILON_DELAY)
                else:
                    debug_msg(f"WTF-3 {self.user_state}")
            else:
                debug_msg("WTF-1")
        else:
            debug_msg(f"clients not matching {self.pending_clients}")

    def got_message(self):
        if self.user_state == UserState.waiting_for_message:
            debug_msg(f"2>3: time = {time.time():.3f}")
            self.send_task = asyncio.create_task(send_new_msg(self))


async def send_new_msg(userData):
    if userData.user_state is not UserState.sending:
        debug_msg('sending')
        # from sending to pending again
        userData.user_state = UserState.sending
        userData.consume_message = userData.message_queue.popleft()
        userData.last_message_clients = userData.pending_clients
        userData.pending_clients = set()
        userData.con_ready_event.set()
        await asyncio.sleep(EPCILON_DELAY)
        userData.con_ready_event.clear()
        userData.msg_ready_event.set()
        await asyncio.sleep(EPCILON_DELAY)
        userData.msg_ready_event.clear()
        userData.user_state = UserState.pending
        if userData.pending_clients and userData.pending_clients == userData.last_message_clients:
            userData.end_the_pending_after(EPCILON_DELAY)
        else:
            userData.end_the_pending_after(PENDING_DELAY_BIG)
        debug_msg(f"pending event finished")
    else:
        debug_msg(f"send called but state is {userData.user_state}")

async def pending_end(userData: UserData):
    userData.pending_end_time = None
    if userData.user_state == UserState.pending:
        # end the connection pending
        # is there any ready message?
        if len(userData.pending_clients)>0:
            if len(userData.message_queue) > 0:
                #debug_msg(f"1>3: time = {time.time():.3f}")
                userData.send_task = asyncio.create_task(send_new_msg(userData))
            else:
                #debug_msg(f"1>2: time = {time.time():.3f}")
                userData.user_state = UserState.waiting_for_message
        else:
            debug_msg("pending end eached with no connection!!")
    else:
        debug_msg("pe", userData.user_state, len(userData.message_queue))


class LongPollable:
    def __init__(self, message_expiration_time=30, is_batch_mode=False):
        # make an asyncio queue for each waiting user
        self.waiting_users: Dict[UserType, UserData] = {}
        self.is_batch_mode = is_batch_mode
        self.tasks = []

    def load_user_data(
        self,
        user: UserType,
    ) -> UserData:
        if user not in self.waiting_users:
            userData = UserData(user_state=UserState.pending)
            self.waiting_users[user] = userData
            return userData
        else:
            return self.waiting_users[user]

    async def wait_for_message(
        self, user: UserType, session: SessoinType, timeout: float
    ) -> TypeLessMessage:

        userData = self.load_user_data(user)
        userData.got_connection(session)
        try:
            await asyncio.wait_for(userData.con_ready_event.wait(), timeout=timeout)
            await asyncio.wait_for(userData.msg_ready_event.wait(), timeout=timeout)

            if self.is_batch_mode:
                # TODO: send all updates in batch after small delay
                raise NotImplementedError()
            else:
                # return consume_message of this user
                # this will work for all waiting connections of this user
                # don't change consume_message here
                # this will broke other connections of this user
                return userData.consume_message
        except asyncio.TimeoutError:
            userData.user_state = UserState.pending
            raise asyncio.TimeoutError()

    async def send_message_no_type(self, user: UserType, messge: Any, event_name):
        msg = TypeLessMessage(event_name=event_name, message=messge)
        userData = self.load_user_data(user)

        userData.message_queue.append(msg)
        userData.got_message()

    def create_message_type(self, event_name: str, schema: Type[T]) -> EventType[T]:
        return EventType(event_name, self)
