package org.nexocam.app

/** Escolhe a rotação física dos pixels, sem apenas trocar o canvas ao redor da cena. */
fun transmissionRotation(
    width: Int,
    height: Int,
    sensorRotation: Int,
    portrait: Boolean,
): Int {
    require(width > 0 && height > 0 && sensorRotation in listOf(0, 90, 180, 270))
    val swapped = sensorRotation == 90 || sensorRotation == 270
    val uprightWidth = if (swapped) height else width
    val uprightHeight = if (swapped) width else height
    if (uprightWidth == uprightHeight) return sensorRotation
    val uprightPortrait = uprightHeight > uprightWidth
    return if (uprightPortrait == portrait) {
        sensorRotation
    } else {
        (sensorRotation + if (portrait) 90 else 270) % 360
    }
}
