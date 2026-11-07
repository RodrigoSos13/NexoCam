package org.nexocam.app

import java.util.ArrayDeque

/** Pequena janela de envio: cobre o tempo de ACK sem acumular vídeo atrasado. */
class PendingFrames {
    private data class Entry(
        val sequence: Long,
        val sentAt: Long,
    )

    private val pending = ArrayDeque<Entry>()
    private var capacity = 1
    private var sequence = 0L
    val available: Boolean get() = synchronized(this) { pending.size < capacity }

    @Synchronized fun reset(capacity: Int = 1) {
        require(capacity in 1..2)
        this.capacity = capacity
        pending.clear()
        sequence = 0
    }

    @Synchronized fun reserve(now: Long): Long? {
        if (pending.size >= capacity) return null
        val next = ++sequence
        pending.addLast(Entry(next, now))
        return next
    }

    @Synchronized fun acknowledge(
        sequence: Long,
        now: Long,
    ): Long {
        val first = pending.peekFirst()
        require(first != null && first.sequence == sequence)
        pending.removeFirst()
        return (now - first.sentAt).coerceAtLeast(0)
    }

    @Synchronized fun rejected(sequence: Long) {
        if (pending.peekLast()?.sequence == sequence) pending.removeLast()
    }
}
