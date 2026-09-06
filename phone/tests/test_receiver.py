"""Standalone Android receiver tests; no BLE, SSH or external services."""
import asyncio
import json
import contextlib
import io
from pathlib import Path
import ssl
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from phone.receiver import ProtocolError, encode_frame, read_frame, receive, tls_context, validate_result, validate_subscribed, validate_session


def result():
    return dict(v=1, type="GESTURE_RESULT", session_id="week7-demo", device_id=1,
                boot_id=4294967295, seq=3, result_id="1:4294967295:3", gesture="POINT", confidence=1.0)


class ContractTests(unittest.IsolatedAsyncioTestCase):
    def test_result_and_subscription_contracts(self):
        self.assertEqual(validate_session("a" * 128), "a" * 128)
        for invalid in ["", "a" * 129, "line\nbreak", "\ud800"]:
            with self.assertRaises(ProtocolError):
                validate_session(invalid)
        self.assertEqual(validate_result(result(), "week7-demo"), result())
        validate_subscribed(dict(v=1, type="SUBSCRIBED", session_id="week7-demo"), "week7-demo")
        for field, value in [("v", True), ("seq", -1), ("boot_id", 2**32),
                             ("confidence", float("nan")), ("confidence", True),
                             ("gesture", "FIST"), ("result_id", "1:2:3"),
                             ("session_id", "elsewhere"), ("extra", 1)]:
            item = result(); item[field] = value
            with self.subTest(field=field), self.assertRaises(ProtocolError):
                validate_result(item, "week7-demo")

    async def test_split_and_coalesced_frames(self):
        stream = asyncio.StreamReader()
        data = encode_frame(result())
        async def feed():
            for value in data:
                stream.feed_data(bytes([value]))
                await asyncio.sleep(0)
            stream.feed_data(data)
        task = asyncio.create_task(feed())
        self.assertEqual(await read_frame(stream), result())
        self.assertEqual(await read_frame(stream), result())
        await task

    async def test_reject_bad_frames(self):
        payloads = [b'{"v":1,"v":1}', b'{"v":NaN}', b'{"v":1e999}', b'[]', b'{} trailing', b'\xff']
        frames = [len(data).to_bytes(4, "big") + data for data in payloads]
        frames += [b'\0\0\0\0', (16385).to_bytes(4, "big"), b'\0\0', b'\0\0\0\x02{']
        for data in frames:
            stream = asyncio.StreamReader(); stream.feed_data(data); stream.feed_eof()
            with self.subTest(data=data), self.assertRaises(ProtocolError):
                await read_frame(stream)

    async def test_incomplete_frame_deadline(self):
        stream = asyncio.StreamReader(); stream.feed_data(b'\0')
        with self.assertRaises(asyncio.TimeoutError):
            await read_frame(stream, timeout=0.02)

    async def test_excessive_integer_is_a_protocol_error_on_every_supported_python(self):
        body = b'{"v":' + b'9' * 5000 + b'}'
        stream = asyncio.StreamReader()
        stream.feed_data(len(body).to_bytes(4, "big") + body)
        with self.assertRaises(ProtocolError):
            await read_frame(stream)


class ReceiverCloseTests(unittest.IsolatedAsyncioTestCase):
    async def receiver_with_writer(self, writer):
        stream = asyncio.StreamReader()
        stream.feed_data(encode_frame(dict(v=1, type="SUBSCRIBED", session_id="week7-demo")))
        stream.feed_data(encode_frame(result()))
        args = SimpleNamespace(ca="unused", port=19999, session="week7-demo", count=1, duration=None)
        with patch("phone.receiver.tls_context", return_value=object()), \
             patch("phone.receiver.asyncio.open_connection", AsyncMock(return_value=(stream, writer))), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return await receive(args)

    async def test_stalled_tls_shutdown_aborts_socket_after_deadline(self):
        writer = ClosingWriter(stall=True)
        summary = await self.receiver_with_writer(writer)
        self.assertEqual(summary["received"], 1)
        self.assertTrue(writer.closed)
        self.assertTrue(writer.aborted, "timed-out close must release its socket")

    async def test_cancellation_during_tls_shutdown_aborts_socket_and_propagates(self):
        writer = ClosingWriter(stall=True)
        task = asyncio.create_task(self.receiver_with_writer(writer))
        await asyncio.wait_for(writer.closing.wait(), 1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(writer.aborted, "cancelled close must release its socket")

    async def test_clean_tls_shutdown_preserves_graceful_close(self):
        writer = ClosingWriter(stall=False)
        self.assertEqual((await self.receiver_with_writer(writer))["received"], 1)
        self.assertTrue(writer.closed)
        self.assertFalse(writer.aborted)


class ClosingWriter:
    """TLS shutdown boundary: no network mock participates in schema validation."""
    def __init__(self, stall):
        self.stall = stall
        self.closed = self.aborted = False
        self.closing = asyncio.Event()
        self.transport = SimpleNamespace(abort=self.abort)

    def write(self, data):
        pass

    async def drain(self):
        pass

    def close(self):
        self.closed = True

    def abort(self):
        self.aborted = True

    async def wait_closed(self):
        self.closing.set()
        if self.stall:
            await asyncio.Event().wait()


class TlsReceiverTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        from tools.generate_week7_pki import generate_pki
        cls.directory = tempfile.TemporaryDirectory(prefix="week7-phone-test-")
        cls.folder = Path(cls.directory.name)
        generate_pki(cls.folder / "pki")
        generate_pki(cls.folder / "wrong")
        cls.server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        cls.server_context.load_cert_chain(cls.folder / "pki/server-cert.pem", cls.folder / "pki/server-key.pem")

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    async def test_actual_tls_receiver_recovers_and_prints_result(self):
        attempts = []
        handlers = set()
        async def handle(reader, writer):
            task = asyncio.current_task(); handlers.add(task)
            try:
                attempts.append(await read_frame(reader))
                writer.write(encode_frame(dict(v=2 if len(attempts) == 1 else 1, type="SUBSCRIBED", session_id="week7-demo")))
                if len(attempts) > 1:
                    writer.write(encode_frame(result()))
                await writer.drain()
                await reader.read()
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass
                handlers.discard(task)
        server = await asyncio.start_server(handle, "127.0.0.1", 0, ssl=self.server_context)
        args = SimpleNamespace(ca=self.folder / "pki/ca-cert.pem", port=server.sockets[0].getsockname()[1],
                               session="week7-demo", count=1, duration=4)
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                summary = await asyncio.wait_for(receive(args), 5)
            self.assertEqual(json.loads(output.getvalue()), result())
            self.assertEqual(summary, dict(received=1, reconnects=1))
            self.assertEqual(attempts, [dict(v=1, type="SUBSCRIBE", session_id="week7-demo")] * 2)
        finally:
            server.close(); await server.wait_closed()
            if handlers:
                await asyncio.gather(*handlers)

    async def test_actual_tls_rejects_wrong_ca_and_wrong_name(self):
        async def handle(reader, writer):
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
        server = await asyncio.start_server(handle, "127.0.0.1", 0, ssl=self.server_context)
        port = server.sockets[0].getsockname()[1]
        try:
            for ca, identity in [("wrong", "ultra96.week7.internal"), ("pki", "wrong.week7.internal")]:
                with self.subTest(ca=ca, identity=identity), self.assertRaises(ssl.SSLCertVerificationError):
                    await asyncio.open_connection("127.0.0.1", port, ssl=tls_context(self.folder / ca / "ca-cert.pem"), server_hostname=identity)
        finally:
            server.close(); await server.wait_closed()


if __name__ == "__main__":
    unittest.main()
