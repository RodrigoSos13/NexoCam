package org.nexocam.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class FramePacerTest {
    @Test fun previewRunsTwiceAsOftenAsTransmissionWithoutEncodingIdleFrames() {
        val preview = FramePacer(33_333_334L)
        val transmission = FramePacer()
        var previewCount = 0
        var encodedCount = 0
        for (frame in 0 until 600) {
            val now = frame * 16_666_667L
            if (preview.acquire(now)) {
                previewCount++
                if (transmission.acquire(now)) encodedCount++
            }
        }
        assertTrue(previewCount in 299..301)
        assertTrue(encodedCount in 149..151)
    }

    @Test fun thirtyFpsCameraWithJitterKeepsFifteenFpsAverage() {
        val pacer = FramePacer()
        val accepted =
            (0 until 300).count { frame ->
                val jitter = if (frame % 2 == 0) 500_000L else -500_000L
                pacer.acquire(frame * 33_333_333L + jitter)
            }
        assertTrue("Capturas em 10 s: $accepted", accepted in 149..151)
    }

    @Test fun longPauseDoesNotCauseBurstOrGrowingBacklog() {
        val pacer = FramePacer(100)
        assertTrue(pacer.acquire(0))
        assertFalse(pacer.acquire(99))
        assertTrue(pacer.acquire(100))
        assertTrue(pacer.acquire(10000))
        assertFalse(pacer.acquire(10000))
        assertFalse(pacer.acquire(10099))
        assertTrue(pacer.acquire(10100))
    }

    @Test fun processingDelaysDoNotMoveEveryFollowingDeadline() {
        val pacer = FramePacer(100)
        val accepted = listOf(0L, 110L, 200L, 310L, 400L).count(pacer::acquire)
        assertEquals(5, accepted)
    }

    @Test fun invalidIntervalIsRejected() {
        assertThrows(IllegalArgumentException::class.java) { FramePacer(0) }
    }
}
