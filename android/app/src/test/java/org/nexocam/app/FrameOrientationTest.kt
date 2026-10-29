package org.nexocam.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class FrameOrientationTest {
    @Test fun landscapeDefaultUsesLandscapePixelsOnPortraitPhone() {
        assertEquals(0, transmissionRotation(640, 480, 90, false))
        assertEquals(90, transmissionRotation(640, 480, 90, true))
        assertEquals(180, transmissionRotation(640, 480, 270, false))
        assertEquals(270, transmissionRotation(640, 480, 270, true))
    }

    @Test fun landscapePhoneAndLiveSwitchUseDifferentPixelRotations() {
        assertEquals(0, transmissionRotation(640, 480, 0, false))
        assertEquals(90, transmissionRotation(640, 480, 0, true))
        assertEquals(180, transmissionRotation(640, 480, 180, false))
        assertEquals(270, transmissionRotation(640, 480, 180, true))
    }

    @Test fun everySensorOrientationProducesTheSelectedAspect() {
        for ((width, height) in listOf(640 to 480, 480 to 640)) {
            for (sensor in listOf(0, 90, 180, 270)) {
                for (portrait in listOf(false, true)) {
                    val rotation = transmissionRotation(width, height, sensor, portrait)
                    val swapped = rotation == 90 || rotation == 270
                    val resultWidth = if (swapped) height else width
                    val resultHeight = if (swapped) width else height
                    assertEquals(portrait, resultHeight > resultWidth)
                }
            }
        }
    }

    @Test fun invalidSensorMetadataRejected() {
        assertThrows(IllegalArgumentException::class.java) { transmissionRotation(640, 480, 45, false) }
        assertThrows(IllegalArgumentException::class.java) { transmissionRotation(0, 480, 90, true) }
    }
}
