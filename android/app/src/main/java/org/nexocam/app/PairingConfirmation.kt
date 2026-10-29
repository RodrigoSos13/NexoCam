package org.nexocam.app

import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeout
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import kotlin.coroutines.resume

suspend fun confirmQrRead(pairing: Pairing): Boolean {
    val client = pinnedClient(pairing)
    var socket: WebSocket? = null
    return try {
        withTimeout(10000) {
            suspendCancellableCoroutine { continuation ->
                var stage = "hello"

                fun finish(success: Boolean) {
                    synchronized(continuation) {
                        if (continuation.isActive) continuation.resume(success)
                    }
                }
                socket =
                    client.newWebSocket(
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
                                webSocket.send(
                                    JSONObject()
                                        .put("v", 1)
                                        .put("type", "hello")
                                        .put("device", "Android NexoCam")
                                        .put("purpose", "pairing")
                                        .toString(),
                                )
                            }

                            override fun onMessage(
                                webSocket: WebSocket,
                                text: String,
                            ) {
                                if (!continuation.isActive) return
                                try {
                                    require(text.length <= 4096)
                                    val message = JSONObject(text)
                                    require(message.getInt("v") == 1)
                                    if (stage == "hello") {
                                        require(message.getString("type") == "hello")
                                        stage = "auth"
                                        webSocket.send(
                                            JSONObject()
                                                .put("v", 1)
                                                .put("type", "authenticate")
                                                .put("token", pairing.token)
                                                .toString(),
                                        )
                                    } else {
                                        require(
                                            message.getString("type") == "state" &&
                                                message.getString("state") == "authenticated",
                                        )
                                        finish(true)
                                    }
                                } catch (_: Exception) {
                                    finish(false)
                                }
                            }

                            override fun onFailure(
                                webSocket: WebSocket,
                                t: Throwable,
                                response: Response?,
                            ) {
                                finish(false)
                            }

                            override fun onClosing(
                                webSocket: WebSocket,
                                code: Int,
                                reason: String,
                            ) {
                                finish(false)
                            }
                        },
                    )
                continuation.invokeOnCancellation { socket?.cancel() }
            }
        }
    } finally {
        socket?.cancel()
        client.dispatcher.cancelAll()
        client.dispatcher.executorService.shutdown()
        client.connectionPool.evictAll()
    }
}
