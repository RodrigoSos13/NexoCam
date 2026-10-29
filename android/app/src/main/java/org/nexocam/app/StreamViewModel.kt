package org.nexocam.app

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class StreamViewModel(
    application: Application,
) : AndroidViewModel(application) {
    private val mutableStatus = MutableStateFlow(R.string.disconnected)
    val status = mutableStatus.asStateFlow()
    private val mutableCamera = MutableStateFlow(false)
    val camera = mutableCamera.asStateFlow()
    private val mutableConnecting = MutableStateFlow(false)
    val connecting = mutableConnecting.asStateFlow()
    private val settings = SettingsRepository(application)
    val lastAddress = settings.lastAddress
    val connection =
        ConnectionManager(viewModelScope) { value ->
            mutableStatus.value = value
            if (value == R.string.connection_error) mutableConnecting.value = false
        }

    fun activateCamera() {
        mutableCamera.value = true
    }

    fun connect(
        address: String,
        fingerprint: String,
        token: String,
    ) {
        try {
            val pairing = parsePairing(address, fingerprint, token)
            mutableConnecting.value = true
            connection.connect(pairing)
            viewModelScope.launch { settings.saveAddress(pairing.address) }
        } catch (error: InvalidPairing) {
            mutableStatus.value =
                when (error.field) {
                    PairingField.ADDRESS -> R.string.invalid_address
                    PairingField.FINGERPRINT -> R.string.invalid_fingerprint
                    PairingField.TOKEN -> R.string.invalid_token
                }
        } catch (_: IllegalArgumentException) {
            mutableStatus.value = R.string.invalid_pairing
        }
    }

    fun disconnect() {
        connection.disconnect()
        mutableConnecting.value = false
        mutableStatus.value = R.string.disconnected
    }

    fun stopCamera() {
        disconnect()
        mutableCamera.value = false
    }

    fun cameraError() {
        viewModelScope.launch {
            stopCamera()
            mutableStatus.value = R.string.camera_error
        }
    }

    override fun onCleared() {
        connection.disconnect()
    }
}
