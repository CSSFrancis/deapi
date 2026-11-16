"""The XY queue's client calls, on the wire: no server needed."""

import struct

import numpy as np
import pytest

from deapi.buffer_protocols import pb
from deapi.client import MAX_SOCKET_TIMEOUT, Client


class _Socket:
    """Collects what the client sends."""

    def __init__(self):
        self.sent = b""
        self.timeout = None

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, data):
        self.sent += data


@pytest.fixture
def client(monkeypatch):
    client = Client()
    client.socket = _Socket()
    client.read_only = False
    replies = []
    monkeypatch.setattr(
        client,
        "_Client__ReceiveResponseForCommand",
        lambda command: replies.pop(0) if replies else True,
    )
    client.replies = replies
    return client


def _command_and_payload(sent):
    size = struct.unpack("I", sent[:4])[0]
    packet = pb.DEPacket()
    packet.ParseFromString(sent[4 : 4 + size])
    return packet.command[0], sent[4 + size :]


def test_append_sends_the_count_then_x_then_y(client):
    points = np.array([[1, 2], [3, 4], [5, 6]])
    assert client.append_xy_array(points) is True
    command, payload = _command_and_payload(client.socket.sent)
    assert (
        command.command_id % 100 == Client.APPEND_SCAN_XY_ARRAY == 46
    )  # the version is the hundreds
    assert [p.p_int for p in command.parameter] == [3]
    assert np.frombuffer(payload, np.int32).tolist() == [1, 3, 5, 2, 4, 6]


def test_end_is_an_empty_append(client):
    assert client.end_xy_queue() is True
    command, payload = _command_and_payload(client.socket.sent)
    assert command.command_id % 100 == 46
    assert [p.p_int for p in command.parameter] == [0]
    assert payload == b""


def test_a_refused_append_is_false(client):
    client.replies.append(False)
    assert client.append_xy_array([[0, 0]]) is False


def test_the_socket_timeout_stays_within_what_a_socket_accepts(client):
    client.exposureTime = 1e6  # a queued scan's exposure is not known when it starts
    assert client._socket_timeout() == MAX_SOCKET_TIMEOUT
    client.exposureTime = 1
    assert client._socket_timeout() == 40
