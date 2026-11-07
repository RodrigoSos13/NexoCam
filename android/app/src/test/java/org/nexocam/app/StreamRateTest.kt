package org.nexocam.app

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class StreamRateTest {
    @Test fun twoFramesRequireExplicitReceiverSupport() {
        assertEquals(2, preferredFrameWindow(JSONObject("""{"max_in_flight":2}""")))
        for (raw in listOf("{}", """{"max_in_flight":100}""", """{"max_in_flight":"2"}""")) {
            assertEquals(1, preferredFrameWindow(JSONObject(raw)))
        }
    }

    @Test fun newReceiverEnablesThirtyFps() {
        assertEquals(30, preferredStreamFps(JSONObject("""{"supported_fps":[15,30]}""")))
        assertEquals(33_333_334L, frameIntervalNanos(30))
    }

    @Test fun oldReceiverKeepsFifteenFps() {
        assertEquals(15, preferredStreamFps(JSONObject("""{"v":1,"type":"hello"}""")))
        assertEquals(15, preferredStreamFps(JSONObject("""{"supported_fps":[15]}""")))
        assertEquals(66_666_667L, frameIntervalNanos(15))
    }

    @Test fun unsupportedOrMalformedRatesNeverEnableThirtyFps() {
        for (raw in listOf(
            """{"supported_fps":[60]}""",
            """{"supported_fps":["30"]}""",
            """{"supported_fps":true}""",
        )) {
            assertEquals(15, preferredStreamFps(JSONObject(raw)))
        }
        assertThrows(IllegalArgumentException::class.java) { frameIntervalNanos(60) }
    }
}
