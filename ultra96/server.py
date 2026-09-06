"""TLS-only Week 7 service. Ingestion ACKs and Phone results use separate ports."""
import argparse
import asyncio
from collections import OrderedDict
import json
import logging
import os
import socket
import ssl
import time

from common.tls import server_context
from common.wire import ProtocolError, STREAM_LIMIT, read_frame, write_frame
from ultra96.protocol import GESTURES, trace_fields, validate_message, validate_session

LOG = logging.getLogger(__name__)
_EXPECTED_ERRORS = (ProtocolError, asyncio.IncompleteReadError, asyncio.TimeoutError,
                    ConnectionError, OSError, ssl.SSLError)


async def _close_writer(writer):
    writer.close()
    try:
        await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
    except (asyncio.TimeoutError, ConnectionError, OSError, ssl.SSLError):
        writer.transport.abort()


class ResultQueue:
    """Live-only bounded queue with monotonic age, shared by one subscriber."""
    def __init__(self):
        self._queue = asyncio.Queue(maxsize=32)
        self.dropped = 0
        self.stale = 0

    def put(self, message, received_at=None):
        if self._queue.full():
            self._queue.get_nowait()
            self.dropped += 1
        self._queue.put_nowait((time.monotonic() if received_at is None else received_at, message))

    async def get(self, now=None):
        _, message = await self.get_timed(now=now)
        return message

    async def get_timed(self, now=None):
        while True:
            received_at, message = await self._queue.get()
            current = time.monotonic() if now is None else now
            if current - received_at >= 2.0:
                self.stale += 1
                continue
            return received_at, message


class Week7Server:
    def __init__(self, ssl_context, session_id="week7-demo", ingest_port=8888, gateway_port=9999):
        if (not isinstance(ssl_context, ssl.SSLContext)
                or ssl_context.minimum_version < ssl.TLSVersion.TLSv1_2):
            raise ValueError("server requires TLS >=1.2")
        self.ssl_context = ssl_context
        self.session_id = validate_session(session_id)
        self.ingest_port = ingest_port
        self.gateway_port = gateway_port
        self._listeners = []
        self._accept_tasks = set()
        self._sockets = set()
        self._tasks = set()
        self._writers = set()
        self._subscriber = None
        self._recent = OrderedDict()
        self._closing = False
        self.metrics = {"accepted": 0, "duplicates": 0, "rejected": 0,
                        "subscribers": 0, "replaced": 0, "disconnected_results": 0,
                        "result_drops": 0, "result_stale": 0, "client_limit": 0}

    async def start(self):
        if self._listeners or self._closing:
            raise RuntimeError("server is already started or closed")
        try:
            for gateway, port in ((False, self.ingest_port), (True, self.gateway_port)):
                listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                listener.setblocking(False)
                self._listeners.append(listener)
                if os.name == "posix":
                    # Match asyncio's POSIX listener default: stopped clients
                    # in TIME_WAIT must not prevent an immediate service restart.
                    # Windows has different reuse semantics and does not need it.
                    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                listener.bind(("127.0.0.1", port))
                listener.listen(8)
                task = asyncio.create_task(self._accept(listener, gateway))
                self._accept_tasks.add(task)
            self.ingest_port = self._listeners[0].getsockname()[1]
            self.gateway_port = self._listeners[1].getsockname()[1]
        except BaseException:
            await self.close()
            raise

    async def _accept(self, listener, gateway):
        loop = asyncio.get_running_loop()
        while not self._closing:
            connection, _ = await loop.sock_accept(listener)
            connection.setblocking(False)
            if self._closing or len(self._sockets) >= 8:
                self.metrics["client_limit"] += 1
                connection.close()
                continue
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._sockets.add(connection)
            task = asyncio.create_task(self._client(connection, gateway))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def _client(self, connection, gateway):
        writer = None
        try:
            loop = asyncio.get_running_loop()
            reader = asyncio.StreamReader(limit=STREAM_LIMIT)
            protocol = asyncio.StreamReaderProtocol(reader)
            transport, _ = await loop.connect_accepted_socket(lambda: protocol, connection,
                ssl=self.ssl_context, ssl_handshake_timeout=5.0)
            writer = asyncio.StreamWriter(transport, protocol, reader, loop)
            transport.set_write_buffer_limits(high=32768, low=16384)
            self._writers.add(writer)
            if gateway:
                await self._gateway(reader, writer)
            else:
                await self._ingest(reader, writer)
        except asyncio.IncompleteReadError:
            pass  # read_frame preserves this only for EOF between complete frames.
        except _EXPECTED_ERRORS:
            self.metrics["rejected"] += 1
        finally:
            try:
                if writer is not None:
                    await _close_writer(writer)
            finally:
                # close() can cancel a client that was already awaiting TLS
                # shutdown here. Always release transport/socket ownership,
                # even when that cancellation interrupts graceful closure.
                try:
                    if writer is not None:
                        writer.transport.abort()
                finally:
                    self._writers.discard(writer)
                    try:
                        connection.close()
                    finally:
                        self._sockets.discard(connection)

    async def _ingest(self, reader, writer):
        while not self._closing:
            message = validate_message(await read_frame(reader), "SENSOR_BATCH", self.session_id)
            trace = (message["device_id"], message["boot_id"], message["seq"])
            duplicate = trace in self._recent
            if duplicate:
                self.metrics["duplicates"] += 1
            else:
                self._recent[trace] = None
                if len(self._recent) > 4096:
                    self._recent.popitem(last=False)
                self.metrics["accepted"] += 1
                LOG.info("accepted session=%s device=%d boot=%d seq=%d",
                         self.session_id, *trace)
                result = dict(v=1, type="GESTURE_RESULT", **trace_fields(message))
                result.update(result_id="{}:{}:{}".format(*trace),
                              gesture=GESTURES[message["seq"] % 4], confidence=1.0)
                if self._subscriber is None:
                    self.metrics["disconnected_results"] += 1
                else:
                    self._subscriber[1].put(result)
            ack = dict(v=1, type="INGEST_ACK", **trace_fields(message))
            ack["status"] = "duplicate" if duplicate else "accepted"
            await write_frame(writer, ack)

    async def _gateway(self, reader, writer):
        validate_message(await read_frame(reader), "SUBSCRIBE", self.session_id)
        queue = ResultQueue()
        owner = (writer, queue)
        previous = self._subscriber
        self._subscriber = owner
        self.metrics["subscribers"] += 1
        if previous is not None:
            self.metrics["replaced"] += 1
            previous[0].close()
        sender = monitor = None
        try:
            await write_frame(writer, {"v": 1, "type": "SUBSCRIBED", "session_id": self.session_id})
            sender = asyncio.create_task(self._send_results(writer, queue))
            # After SUBSCRIBE the connection is receive-only; EOF or extra bytes end ownership.
            monitor = asyncio.create_task(reader.read(1))
            finished, _ = await asyncio.wait((sender, monitor), return_when=asyncio.FIRST_COMPLETED)
            for task in finished:
                task.result()
        finally:
            if self._subscriber is owner:
                self._subscriber = None
            for task in (sender, monitor):
                if task is not None:
                    task.cancel()
            await asyncio.gather(*(task for task in (sender, monitor) if task is not None),
                                 return_exceptions=True)
            self.metrics["result_drops"] += queue.dropped
            self.metrics["result_stale"] += queue.stale

    async def _send_results(self, writer, queue):
        while True:
            received_at, result = await queue.get_timed()
            remaining = 2.0 - (time.monotonic() - received_at)
            if remaining <= 0:
                queue.stale += 1
                continue
            # A drain deadline bounds our own backlog. Bytes already handed to
            # TCP/TLS cannot be retracted, so receiver rendering age is separate.
            await write_frame(writer, result, timeout=remaining)

    async def close(self):
        self._closing = True
        for task in self._accept_tasks:
            task.cancel()
        await asyncio.gather(*self._accept_tasks, return_exceptions=True)
        self._accept_tasks.clear()
        for listener in self._listeners:
            listener.close()
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._listeners.clear()
        self._subscriber = None
        self._recent.clear()


async def _run(args):
    service = Week7Server(server_context(args.cert, args.key), session_id=args.session_id,
                          ingest_port=args.ingest_port, gateway_port=args.gateway_port)
    await service.start()
    print(json.dumps({"event": "listening", "host": "127.0.0.1", "tls": True,
                      "ingest_port": service.ingest_port, "gateway_port": service.gateway_port}), flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await service.close()
        print(json.dumps({"event": "stopped", "metrics": service.metrics}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cert", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--session-id", default="week7-demo")
    parser.add_argument("--ingest-port", type=int, default=8888)
    parser.add_argument("--gateway-port", type=int, default=9999)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
