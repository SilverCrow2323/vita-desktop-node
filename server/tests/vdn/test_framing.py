import asyncio
import unittest

from vdn.protocol.framing import (
    FrameError,
    decode_frame,
    decode_payload,
    encode_frame,
    read_frame,
    write_frame,
)

REQUEST = {
    "protocol": "VDN2",
    "version": 2,
    "type": "request",
    "id": "test-1",
    "method": "node.capabilities",
    "params": {},
}


class FramingTests(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(decode_frame(encode_frame(REQUEST)), REQUEST)

    def test_unicode_round_trip(self):
        message = dict(REQUEST, params={"label": "Vita – nodo"})
        self.assertEqual(decode_frame(encode_frame(message)), message)

    def test_rejects_wrong_protocol(self):
        with self.assertRaises(FrameError):
            encode_frame(dict(REQUEST, protocol="VMON1"))

    def test_rejects_wrong_version(self):
        with self.assertRaises(FrameError):
            encode_frame(dict(REQUEST, version=99))

    def test_rejects_missing_method(self):
        message = dict(REQUEST)
        del message["method"]
        with self.assertRaises(FrameError):
            encode_frame(message)

    def test_rejects_non_object_params(self):
        with self.assertRaises(FrameError):
            encode_frame(dict(REQUEST, params=[]))

    def test_rejects_oversized_frame(self):
        with self.assertRaises(FrameError):
            encode_frame(dict(REQUEST, params={"padding": "x" * 100}), max_frame=32)

    def test_rejects_truncated_and_trailing_data(self):
        frame = encode_frame(REQUEST)
        with self.assertRaises(FrameError):
            decode_frame(frame[:-1])
        with self.assertRaises(FrameError):
            decode_frame(frame + b"x")

    def test_rejects_non_standard_json_numeric_constants(self):
        for constant in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(constant=constant):
                payload = (
                    b'{"protocol":"VDN2","version":2,"type":"request",'
                    b'"id":"test-1","method":"node.capabilities",'
                    b'"params":{"value":' + constant + b'}}'
                )
                with self.assertRaises(FrameError):
                    decode_payload(payload)

    def test_rejects_zero_length(self):
        with self.assertRaises(FrameError):
            decode_frame(b"\x00\x00\x00\x00")


class AsyncFramingTests(unittest.IsolatedAsyncioTestCase):
    async def test_stream_read_write(self):
        reader = asyncio.StreamReader()
        class Writer:
            def __init__(self):
                self.data = bytearray()
            def write(self, data):
                self.data.extend(data)
            async def drain(self):
                return None

        writer = Writer()
        await write_frame(writer, REQUEST)
        reader.feed_data(bytes(writer.data))
        self.assertEqual(await read_frame(reader), REQUEST)

    async def test_incomplete_stream_is_rejected(self):
        reader = asyncio.StreamReader()
        reader.feed_data(b"\x00\x00")
        reader.feed_eof()
        with self.assertRaises(FrameError):
            await read_frame(reader)


if __name__ == "__main__":
    unittest.main()
