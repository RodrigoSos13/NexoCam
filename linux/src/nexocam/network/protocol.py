"""Contrato inicial de controle; ainda sem servidor de rede."""

import json

VERSION = 1
MAX_CONTROL_BYTES = 4096
MAX_FRAME_BYTES = 1024 * 1024
TYPES = {"hello", "authenticate", "configure", "start", "state", "stop", "error"}


class ProtocolError(ValueError):
    pass


def parse_control(raw: str) -> dict:
    if len(raw.encode("utf-8")) > MAX_CONTROL_BYTES:
        raise ProtocolError("Mensagem de controle excede o limite.")
    try:
        value = json.loads(raw)
    except (ValueError, RecursionError) as exc:
        raise ProtocolError("JSON inválido.") from exc
    if not isinstance(value, dict):
        raise ProtocolError("Controle deve ser um objeto JSON.")
    if type(value.get("v")) is not int or value["v"] != VERSION:
        raise ProtocolError("Versão de protocolo incompatível.")
    if not isinstance(value.get("type"), str) or value["type"] not in TYPES:
        raise ProtocolError("Tipo de mensagem desconhecido.")
    return value
