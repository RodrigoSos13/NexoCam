import pytest

from nexocam.network.firewall import ufw_rule


def test_rule_uses_network_instead_of_phone_ip():
    rule = ufw_rule("wlan0", "192.168.3.5", "255.255.255.0", 8765)
    assert rule[rule.index("from") + 1] == "192.168.3.0/24"
    assert rule[rule.index("on") + 1] == "wlan0"
    assert rule[rule.index("port") + 1] == "8765"
    assert "192.168.83.111" not in rule


@pytest.mark.parametrize(
    "interface,address,mask,port",
    [
        ("wlan0;id", "192.168.3.5", "255.255.255.0", 8765),
        ("wlan0", "192.168.3.5", "0.0.0.0", 8765),
        ("lo", "127.0.0.1", "255.0.0.0", 8765),
        ("wlan0", "192.168.3.5", "255.255.255.0", 0),
    ],
)
def test_reject_invalid_rule(interface, address, mask, port):
    with pytest.raises(ValueError):
        ufw_rule(interface, address, mask, port)
