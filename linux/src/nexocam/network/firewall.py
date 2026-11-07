"""Regra UFW limitada à interface e sub-rede escolhidas no pareamento."""

import ipaddress
import re


def ufw_rule(interface: str, address: str, netmask: str, port: int) -> list[str]:
    if not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,15}", interface):
        raise ValueError("Interface de rede inválida.")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Porta inválida.")
    network = ipaddress.IPv4Network(f"{address}/{netmask}", strict=False)
    if network.prefixlen == 0 or network.is_loopback or network.is_multicast:
        raise ValueError("Selecione uma rede local válida.")
    return [
        "allow",
        "in",
        "on",
        interface,
        "from",
        str(network),
        "to",
        "any",
        "port",
        str(port),
        "proto",
        "tcp",
        "comment",
        "NexoCam rede local",
    ]
