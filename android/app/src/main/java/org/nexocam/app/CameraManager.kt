package org.nexocam.app

import android.content.Context
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
        ready: () -> Boolean,
        portrait: () -> Boolean,
        frame: (ByteArray) -> Unit,
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
                var last = 0L
                analyzer.setAnalyzer(executor) { image ->
                    try {
                        val now = System.nanoTime()
                        if (!stopped.get() && ready() && now - last >= 66_666_667L) {
                            last = now
                            frame(processor.jpeg(image, portrait()))
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
