package org.nexocam.app

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class PairingQrTest {
    private fun payload(): JSONObject =
        JSONObject()
            .put("v", 1)
            .put("host", "192.0.2.10")
            .put("port", 8765)
            .put("fingerprint", "a".repeat(64))
            .put("token", "b".repeat(64))

    @Test fun validQrFillsPairing() {
        val pairing = parsePairingQr("nexocam:pair:v1:" + payload())
        assertEquals("192.0.2.10", pairing.address)
        assertEquals("a".repeat(64), pairing.fingerprint)
        assertEquals("b".repeat(64), pairing.token)
    }

    @Test fun rejectsForeignVersionsPortsAndInvalidCredentials() {
        for (raw in listOf(
            "https://example.com",
            "nexocam:pair:v1:" + "x".repeat(1025),
            "nexocam:pair:v1:" + payload().put("v", 2),
            "nexocam:pair:v1:" + payload().put("port", 80),
            "nexocam:pair:v1:" + payload().put("fingerprint", "invalid"),
            "nexocam:pair:v1:" + payload().put("host", "example.com"),
            "nexocam:pair:v1:" + payload().put("extra", "unexpected"),
        )) {
            assertThrows(Exception::class.java) { parsePairingQr(raw) }
        }
    }
}
