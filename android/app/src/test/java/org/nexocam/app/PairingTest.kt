package org.nexocam.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Test
import java.security.MessageDigest
import java.security.cert.CertificateException
import java.security.cert.CertificateFactory
import java.security.cert.X509Certificate

class PairingTest {
    private val fingerprint = "a".repeat(64)
    private val token = "b".repeat(64)

    @Test fun validAddressAndCredentials() {
        assertEquals("192.168.1.2", Pairing("192.168.1.2", fingerprint, token).address)
        assertFalse(Pairing("127.0.0.1", fingerprint, token).toString().contains(token))
    }

    @Test fun invalidMaterialRejected() {
        for (address in listOf("", "example.com", "256.1.1.1", "1.2.3", "1.2.3.4/path", "1.2.3.-1")) {
            assertThrows(IllegalArgumentException::class.java) { Pairing(address, fingerprint, token) }
        }
        assertThrows(IllegalArgumentException::class.java) { Pairing("127.0.0.1", "x".repeat(64), token) }
        assertThrows(IllegalArgumentException::class.java) { Pairing("127.0.0.1", fingerprint, "short") }
    }

    @Test fun onlyPinnedCertificateAccepted() {
        val certificate =
            javaClass.getResourceAsStream("/server.crt").use {
                CertificateFactory.getInstance("X.509").generateCertificate(it) as X509Certificate
            }
        val pin =
            MessageDigest
                .getInstance("SHA-256")
                .digest(certificate.encoded)
                .joinToString("") { "%02x".format(it) }
        PinnedTrustManager(pin).checkServerTrusted(arrayOf(certificate), "EC")
        assertThrows(CertificateException::class.java) {
            PinnedTrustManager("0".repeat(64)).checkServerTrusted(arrayOf(certificate), "EC")
        }
        assertThrows(CertificateException::class.java) {
            PinnedTrustManager(pin).checkServerTrusted(emptyArray(), "EC")
        }
    }
}
