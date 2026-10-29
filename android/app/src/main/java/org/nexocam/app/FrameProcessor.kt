package org.nexocam.app

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.ImageFormat
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.YuvImage
import androidx.camera.core.ImageProxy
import androidx.core.graphics.createBitmap
import java.io.ByteArrayOutputStream

class FrameProcessor {
    fun jpeg(
        image: ImageProxy,
        portrait: Boolean = false,
    ): ByteArray {
        val width = image.width
        val height = image.height
        val nv21 = ByteArray(width * height * 3 / 2)

        fun sample(
            plane: ImageProxy.PlaneProxy,
            row: Int,
            col: Int,
        ): Byte = plane.buffer.get(plane.buffer.position() + row * plane.rowStride + col * plane.pixelStride)
        for (y in 0 until height) {
            for (x in 0 until width) {
                nv21[y * width + x] = sample(image.planes[0], y, x)
            }
        }
        var index = width * height
        for (y in 0 until height / 2) {
            for (x in 0 until width / 2) {
                nv21[index++] = sample(image.planes[2], y, x)
                nv21[index++] = sample(image.planes[1], y, x)
            }
        }
        val intermediate = ByteArrayOutputStream()
        check(
            YuvImage(nv21, ImageFormat.NV21, width, height, null)
                .compressToJpeg(Rect(0, 0, width, height), 90, intermediate),
        )
        val bytes = intermediate.toByteArray()
        val bitmap =
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                ?: error("Falha ao converter YUV")
        val degrees = transmissionRotation(width, height, image.imageInfo.rotationDegrees, portrait)
        val matrix = Matrix().apply { postRotate(degrees.toFloat()) }
        val rotated = Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
        val outputWidth = if (portrait) 480 else 640
        val outputHeight = if (portrait) 640 else 480
        val output = createBitmap(outputWidth, outputHeight)
        try {
            val canvas = Canvas(output)
            canvas.drawColor(Color.BLACK)
            val scale = minOf(outputWidth.toFloat() / rotated.width, outputHeight.toFloat() / rotated.height)
            val w = rotated.width * scale
            val h = rotated.height * scale
            canvas.drawBitmap(
                rotated,
                null,
                RectF(
                    (outputWidth - w) / 2,
                    (outputHeight - h) / 2,
                    (outputWidth + w) / 2,
                    (outputHeight + h) / 2,
                ),
                Paint(Paint.FILTER_BITMAP_FLAG),
            )
            return ByteArrayOutputStream().use { buffer ->
                check(output.compress(Bitmap.CompressFormat.JPEG, 75, buffer))
                buffer.toByteArray()
            }
        } finally {
            if (rotated !== bitmap) rotated.recycle()
            bitmap.recycle()
            output.recycle()
        }
    }
}
