package org.nexocam.app

import java.net.InetAddress
import java.net.Socket
import javax.net.SocketFactory

/** Envia os fragmentos de vídeo sem a espera do algoritmo de Nagle. TLS permanece separado. */
class LowLatencySocketFactory(
    private val delegate: SocketFactory = SocketFactory.getDefault(),
) : SocketFactory() {
    override fun createSocket(): Socket = delegate.createSocket().apply { tcpNoDelay = true }

    override fun createSocket(
        host: String,
        port: Int,
    ): Socket = delegate.createSocket(host, port).apply { tcpNoDelay = true }

    override fun createSocket(
        host: InetAddress,
        port: Int,
    ): Socket = delegate.createSocket(host, port).apply { tcpNoDelay = true }

    override fun createSocket(
        host: String,
        port: Int,
        localHost: InetAddress,
        localPort: Int,
    ): Socket = delegate.createSocket(host, port, localHost, localPort).apply { tcpNoDelay = true }

    override fun createSocket(
        host: InetAddress,
        port: Int,
        localHost: InetAddress,
        localPort: Int,
    ): Socket = delegate.createSocket(host, port, localHost, localPort).apply { tcpNoDelay = true }
}
