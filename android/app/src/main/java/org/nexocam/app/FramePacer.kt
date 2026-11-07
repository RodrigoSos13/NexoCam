package org.nexocam.app

/** Mantém o ritmo sem acumular atraso nem descartar um quadro extra por jitter da câmera. */
class FramePacer(
    private val intervalNanos: Long = 66_666_667L,
) {
    private var deadline: Long? = null

    init {
        require(intervalNanos > 0)
    }

    fun acquire(now: Long): Boolean {
        val next = deadline
        if (next != null && now < next) return false
        deadline = if (next == null || now - next >= intervalNanos) now + intervalNanos else next + intervalNanos
        return true
    }
}
