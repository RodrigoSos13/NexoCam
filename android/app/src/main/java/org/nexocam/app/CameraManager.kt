package org.nexocam.app

import android.content.Context
import android.util.Log
import android.util.Size
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class CameraManager(
    private val context: Context,
) {
    private val executor = Executors.newSingleThreadExecutor()
    private val processor = FrameProcessor()
    private val stopped = AtomicBoolean(false)
    private var provider: ProcessCameraProvider? = null
    private var analysis: ImageAnalysis? = null

    fun start(
        owner: LifecycleOwner,
        view: PreviewView,
        front: Boolean,
        readyToSend: () -> Boolean,
        transmissionFps: () -> Int,
        portrait: () -> Boolean,
        frame: (PreparedFrame) -> Unit,
        error: () -> Unit,
    ) {
        val future = ProcessCameraProvider.getInstance(context)
        future.addListener({
            if (stopped.get()) return@addListener
            try {
                val cameraProvider = future.get()
                provider = cameraProvider
                val selector = if (front) CameraSelector.DEFAULT_FRONT_CAMERA else CameraSelector.DEFAULT_BACK_CAMERA
                check(cameraProvider.hasCamera(selector))
                val preview = Preview.Builder().build().apply { setSurfaceProvider(view.surfaceProvider) }
                val analyzer =
                    ImageAnalysis
                        .Builder()
                        .setResolutionSelector(
                            ResolutionSelector
                                .Builder()
                                .setResolutionStrategy(
                                    ResolutionStrategy(
                                        Size(640, 480),
                                        ResolutionStrategy.FALLBACK_RULE_CLOSEST_LOWER_THEN_HIGHER,
                                    ),
                                ).build(),
                        ).setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .build()
                analysis = analyzer
                val pacer = FramePacer(33_333_334L)
                var sendFps = 15
                var transmissionPacer = FramePacer(frameIntervalNanos(sendFps))
                var measuredFrom = System.nanoTime()
                var measuredFrames = 0
                var encodedFrames = 0
                var processingNanos = 0L
                var longestNanos = 0L
                analyzer.setAnalyzer(executor) { image ->
                    try {
                        val now = System.nanoTime()
                        if (!stopped.get() && pacer.acquire(now)) {
                            val negotiatedFps = transmissionFps()
                            if (negotiatedFps != sendFps) {
                                sendFps = negotiatedFps
                                transmissionPacer = FramePacer(frameIntervalNanos(sendFps))
                            }
                            val encode = readyToSend() && transmissionPacer.acquire(now)
                            frame(processor.process(image, portrait(), encode))
                            if (encode) encodedFrames++
                            val finished = System.nanoTime()
                            val elapsed = finished - now
                            measuredFrames++
                            processingNanos += elapsed
                            longestNanos = maxOf(longestNanos, elapsed)
                            if (finished - measuredFrom >= 5_000_000_000L) {
                                // Somente medidas agregadas; nunca imagens ou dados do pareamento.
                                Log.d(
                                    "NexoCamPerf",
                                    "capture=${image.width}x${image.height} " +
                                        "fps=${measuredFrames * 1_000_000_000.0 / (finished - measuredFrom)} " +
                                        "encoded_fps=${encodedFrames * 1_000_000_000.0 / (finished - measuredFrom)} " +
                                        "processing_ms=${processingNanos / measuredFrames / 1_000_000.0} " +
                                        "max_ms=${longestNanos / 1_000_000.0}",
                                )
                                measuredFrom = finished
                                measuredFrames = 0
                                encodedFrames = 0
                                processingNanos = 0
                                longestNanos = 0
                            }
                        }
                    } catch (_: Exception) {
                        error()
                    } finally {
                        image.close()
                    }
                }
                cameraProvider.bindToLifecycle(owner, selector, preview, analyzer)
            } catch (_: Exception) {
                error()
            }
        }, ContextCompat.getMainExecutor(context))
    }

    fun stop() {
        stopped.set(true)
        analysis?.clearAnalyzer()
        provider?.unbindAll()
        executor.shutdown()
    }
}
