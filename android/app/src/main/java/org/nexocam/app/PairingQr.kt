package org.nexocam.app

import org.json.JSONObject

fun parsePairingQr(raw: String): Pairing {
    require(raw.length <= 1024 && raw.startsWith("nexocam:pair:v1:"))
    val data = JSONObject(raw.removePrefix("nexocam:pair:v1:"))
    require(data.get("v") == 1 && data.get("port") == 8765)
    require(data.keys().asSequence().toSet() == setOf("v", "host", "port", "fingerprint", "token"))
    return parsePairing(data.getString("host"), data.getString("fingerprint"), data.getString("token"))
}
