package org.nexocam.app

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class LowLatencySocketTest {
    @Test fun pinnedTransportEnablesNoDelayBeforeConnecting() {
        val client = pinnedClient(Pairing("127.0.0.1", "0".repeat(64), "1".repeat(64)))
        try {
            client.socketFactory.createSocket().use { socket ->
                assertFalse(socket.isConnected)
                assertTrue(socket.tcpNoDelay)
            }
            assertFalse(client.followRedirects)
            assertFalse(client.followSslRedirects)
        } finally {
            client.dispatcher.executorService.shutdown()
            client.connectionPool.evictAll()
        }
    }
}
