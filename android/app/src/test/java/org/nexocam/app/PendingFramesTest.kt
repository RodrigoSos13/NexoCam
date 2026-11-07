package org.nexocam.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.ArrayDeque

class PendingFramesTest {
    @Test fun boundedWindowAcceptsTwoAndRejectsThird() {
        val window = PendingFrames()
        window.reset(2)
        assertEquals(1L, window.reserve(0))
        assertEquals(2L, window.reserve(10))
        assertFalse(window.available)
        assertNull(window.reserve(20))
        assertEquals(40L, window.acknowledge(1, 40))
        assertTrue(window.available)
        assertEquals(3L, window.reserve(50))
    }

    @Test fun duplicateAndOutOfOrderAcknowledgementsAreRejected() {
        val window = PendingFrames()
        window.reset(2)
        window.reserve(0)
        window.reserve(10)
        assertThrows(IllegalArgumentException::class.java) { window.acknowledge(2, 30) }
        window.acknowledge(1, 40)
        assertThrows(IllegalArgumentException::class.java) { window.acknowledge(1, 50) }
        window.acknowledge(2, 60)
        assertThrows(IllegalArgumentException::class.java) { window.acknowledge(3, 70) }
    }

    @Test fun resetAndFailedSendReleaseSlots() {
        val window = PendingFrames()
        val sequence = window.reserve(0)!!
        window.rejected(sequence)
        assertTrue(window.available)
        window.reserve(10)
        window.reset()
        assertEquals(1L, window.reserve(20))
        assertNull(window.reserve(30))
        assertThrows(IllegalArgumentException::class.java) { window.reset(3) }
    }

    @Test fun twoSlotsSustainThirtyFpsWithFortyMillisecondAck() {
        fun simulate(capacity: Int): Int {
            val window = PendingFrames()
            window.reset(capacity)
            val acknowledgements = ArrayDeque<Pair<Long, Long>>()
            var sent = 0
            for (frame in 0 until 60) {
                val now = frame * 33_333_334L
                while (acknowledgements.peekFirst()?.second?.let { it <= now } == true) {
                    window.acknowledge(acknowledgements.removeFirst().first, now)
                }
                window.reserve(now)?.let {
                    acknowledgements.addLast(it to now + 40_000_000L)
                    sent++
                }
            }
            return sent
        }
        assertEquals(30, simulate(1))
        assertEquals(60, simulate(2))
    }
}
