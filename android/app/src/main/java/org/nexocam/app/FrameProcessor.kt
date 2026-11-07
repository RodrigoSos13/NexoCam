package org.nexocam.app

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import androidx.camera.core.ImageProxy
import androidx.core.graphics.createBitmap
import java.io.ByteArrayOutputStream

data class PreparedFrame(
    val jpeg: ByteArray?,
    val preview: Bitmap,
)

class FrameProcessor {
    private val paint = Paint(Paint.FILTER_BITMAP_FLAG)
    private val encoded = ByteArrayOutputStream(65536)

    fun process(
        image: ImageProxy,
        portrait: Boolean = false,
        encode: Boolean = true,
        width: Int = 640,
        height: Int = 480,
        quality: Int = 75,
    ): PreparedFrame {
        // CameraX converte YUV diretamente; não há JPEG intermediário nem loop por pixel em Kotlin.
        val source = image.toBitmap()
        val outputWidth = if (portrait) height else width
        val outputHeight = if (portrait) width else height
        var output: Bitmap? = null
        try {
            val degrees = transmissionRotation(source.width, source.height, image.imageInfo.rotationDegrees, portrait)
            val swapped = degrees == 90 || degrees == 270
            val rotatedWidth = if (swapped) source.height else source.width
            val rotatedHeight = if (swapped) source.width else source.height
            val scale = minOf(outputWidth.toFloat() / rotatedWidth, outputHeight.toFloat() / rotatedHeight)
            val bitmap = createBitmap(outputWidth, outputHeight)
            output = bitmap
            Canvas(bitmap).apply {
                drawColor(Color.BLACK)
                translate(outputWidth / 2f, outputHeight / 2f)
                rotate(degrees.toFloat())
                scale(scale, scale)
                translate(-source.width / 2f, -source.height / 2f)
                drawBitmap(source, 0f, 0f, paint)
            }
            val jpeg =
                if (encode) {
                    encoded.reset()
                    check(bitmap.compress(Bitmap.CompressFormat.JPEG, quality, encoded))
                    encoded.toByteArray()
                } else {
                    null
                }
            // A prévia usa os mesmos pixels preparados, sem descomprimir o JPEG no celular.
            return PreparedFrame(jpeg, bitmap)
        } catch (error: Exception) {
            output?.recycle()
            throw error
        } finally {
            source.recycle()
        }
    }
}
