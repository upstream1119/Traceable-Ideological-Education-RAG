import socket

import pytest

from scripts.run_local import SERVICE, check_environment, port_available, read_health
from src.api.main import health


def test_port_conflict_is_rejected_without_stopping_its_owner():
    with socket.socket() as owner:
        owner.bind(("127.0.0.1", 0))
        owner.listen()
        port = owner.getsockname()[1]
        with pytest.raises(RuntimeError, match="不要关闭未知进程"):
            port_available(port)
        assert owner.getsockname()[1] == port
        assert owner.fileno() >= 0


def test_equal_ports_are_rejected_before_starting():
    with pytest.raises(RuntimeError, match="端口必须不同"):
        check_environment(8000, 8000)


def test_health_identity_matches_launcher_and_does_not_expose_secrets():
    assert health() == {"status": "ok", "service": SERVICE}
