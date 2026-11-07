package org.nexocam.app

import org.json.JSONObject

fun preferredFrameWindow(hello: JSONObject): Int = if (hello.opt("max_in_flight") == 2) 2 else 1

fun preferredStreamFps(hello: JSONObject): Int {
    val supported = hello.optJSONArray("supported_fps") ?: return 15
    return if ((0 until supported.length()).any { supported.opt(it) == 30 }) 30 else 15
}

fun frameIntervalNanos(fps: Int): Long {
    require(fps == 15 || fps == 30)
    return (1_000_000_000L + fps - 1) / fps
}
