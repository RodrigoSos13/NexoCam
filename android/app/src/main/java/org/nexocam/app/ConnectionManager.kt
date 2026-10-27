package org.nexocam.app

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okio.ByteString.Companion.toByteString
import org.json.JSONObject
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import kotlin.coroutines.resume

class ConnectionManager(
    private val scope: CoroutineScope,
    private val status: (Int) -> Unit,
) {
    @Volatile private var socket: WebSocket? = null

    @Volatile var streaming = false
        private set
    private var job: Job? = null
    private var client: OkHttpClient? = null
    private val sequence = AtomicLong()
    private val inFlight = AtomicBoolean(false)
    val canSend: Boolean get() = streaming && !inFlight.get()

    fun connect(pairing: Pairing) {
        disconnect()
        val transport = pinnedClient(pairing)
        client = transport
        job =
            scope.launch {
                var attempt = 0
                while (isActive) {
                    status(if (attempt == 0) R.string.connecting else R.string.reconnecting)
                    val retry = session(transport, pairing)
                    if (!retry) {
                        status(R.string.connection_error)
                        break
                    }
                    delay((1000L shl attempt.coerceAtMost(5)).coerceAtMost(30000) + (0..500).random())
                    attempt++
                }
            }
    }

    private suspend fun session(
        transport: OkHttpClient,
        pairing: Pairing,
    ): Boolean =
        suspendCancellableCoroutine { continuation ->
            inFlight.set(false)
            var stage = "hello"
            var ended = false

            fun end(retry: Boolean) {
                synchronized(continuation) {
                    if (ended || !continuation.isActive) return
                    ended = true
                    streaming = false
                    if (continuation.isActive) continuation.resume(retry)
                }
            }

            fun send(
                ws: WebSocket,
                kind: String,
                fields: JSONObject = JSONObject(),
            ) {
                fields.put("v", 1).put("type", kind)
                ws.send(fields.toString())
            }
            val ws =
                transport.newWebSocket(
                    Request.Builder().url("wss://nexocam.local:8765").build(),
                    object : WebSocketListener() {
                        override fun onOpen(
                            webSocket: WebSocket,
                            response: Response,
                        ) {
                            if (!continuation.isActive) {
                                webSocket.cancel()
                                return
                            }
                            status(R.string.authenticating)
                            send(webSocket, "hello", JSONObject().put("device", "Android NexoCam"))
                        }

                        override fun onMessage(
                            webSocket: WebSocket,
                            text: String,
                        ) {
                            if (!continuation.isActive) return
                            try {
                                require(text.toByteArray().size <= 4096)
                                val obj = JSONObject(text)
                                require(obj.getInt("v") == 1)
                                when (stage) {
                                    "hello" -> {
                                        require(obj.getString("type") == "hello")
                                        stage = "auth"
                                        send(webSocket, "authenticate", JSONObject().put("token", pairing.token))
                                    }
                                    "auth" -> {
                                        require(
                                            obj.getString("type") == "state" &&
                                                obj.getString("state") == "authenticated",
                                        )
                                        stage = "config"
                                        send(
                                            webSocket,
                                            "configure",
                                            JSONObject()
                                                .put("width", 640)
                                                .put("height", 480)
                                                .put("fps", 15)
                                                .put("codec", "jpeg"),
                                        )
                                    }
                                    "config" -> {
                                        require(
                                            obj.getString("type") == "configure" &&
                                                obj.getInt("width") == 640 &&
                                                obj.getInt("height") == 480 &&
                                                obj.getInt("fps") == 15 &&
                                                obj.getString("codec") == "jpeg",
                                        )
                                        stage = "start"
                                        send(webSocket, "start")
                                    }
                                    "start" -> {
                                        require(
                                            obj.getString("type") == "state" && obj.getString("state") == "streaming",
                                        )
                                        stage = "streaming"
                                        streaming = true
                                        status(R.string.streaming)
                                    }
                                    "streaming" -> {
                                        require(
                                            obj.getString("type") == "state" &&
                                                obj.getString("state") == "frame" &&
                                                obj.getLong("sequence") == sequence.get(),
                                        )
                                        inFlight.set(false)
                                    }
                                    else -> error("Controle inesperado")
                                }
                            } catch (_: Exception) {
                                webSocket.cancel()
                                end(false)
                            }
                        }

                        override fun onFailure(
                            webSocket: WebSocket,
                            t: Throwable,
                            response: Response?,
                        ) {
                            end(t !is javax.net.ssl.SSLException)
                        }

                        override fun onClosing(
                            webSocket: WebSocket,
                            code: Int,
                            reason: String,
                        ) {
                            webSocket.close(code, null)
                            end(code != 1008 && code != 1009)
                        }

                        override fun onClosed(
                            webSocket: WebSocket,
                            code: Int,
                            reason: String,
                        ) {
                            end(code != 1008 && code != 1009)
                        }
                    },
                )
            socket = ws
            continuation.invokeOnCancellation {
                ws.cancel()
                streaming = false
            }
        }

    fun send(jpeg: ByteArray) {
        val ws = socket ?: return
        if (!streaming ||
            ws.queueSize() != 0L ||
            jpeg.size > 1048576 - 21 ||
            !inFlight.compareAndSet(false, true)
        ) {
            return
        }
        val packet =
            ByteBuffer
                .allocate(21 + jpeg.size)
                .put(byteArrayOf(78, 88, 67, 70))
                .put(1.toByte())
                .putLong(sequence.incrementAndGet())
                .putLong(System.nanoTime() / 1000)
                .put(jpeg)
                .array()
        if (!ws.send(packet.toByteString())) inFlight.set(false)
    }

    fun disconnect() {
        job?.cancel()
        job = null
        streaming = false
        inFlight.set(false)
        socket?.cancel()
        socket = null
        client?.dispatcher?.cancelAll()
        client?.dispatcher?.executorService?.shutdown()
        client?.connectionPool?.evictAll()
        client = null
    }
}
