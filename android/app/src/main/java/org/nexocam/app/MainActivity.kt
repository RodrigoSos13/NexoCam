package org.nexocam.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions

class MainActivity : ComponentActivity() {
    private val model: StreamViewModel by viewModels()
    private val permission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) model.activateCamera()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                Surface(Modifier.fillMaxSize()) {
                    Screen(model) {
                        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) ==
                            PackageManager.PERMISSION_GRANTED
                        ) {
                            model.activateCamera()
                        } else {
                            permission.launch(Manifest.permission.CAMERA)
                        }
                    }
                }
            }
        }
    }

    override fun onStop() {
        model.stopCamera()
        super.onStop()
    }
}

@Composable
private fun Screen(
    model: StreamViewModel,
    activate: () -> Unit,
) {
    val context = LocalContext.current
    val keyboard = LocalSoftwareKeyboardController.current
    val camera by model.camera.collectAsStateWithLifecycle()
    val connecting by model.connecting.collectAsStateWithLifecycle()
    val status by model.status.collectAsStateWithLifecycle()
    val savedAddress by model.lastAddress.collectAsStateWithLifecycle(initialValue = "")
    var address by remember { mutableStateOf("") }
    var fingerprint by remember { mutableStateOf("") }
    // Segredo somente na memória desta tela, sem saved state ou DataStore.
    var token by remember { mutableStateOf("") }
    var front by remember { mutableStateOf(false) }
    var scanRequested by remember { mutableStateOf(false) }
    val scanner =
        rememberLauncherForActivityResult(ScanContract()) { result ->
            val raw = result.contents
            if (raw != null) {
                try {
                    val pairing = parsePairingQr(raw)
                    address = pairing.address
                    fingerprint = pairing.fingerprint
                    token = pairing.token
                    Toast.makeText(context, R.string.qr_loaded, Toast.LENGTH_LONG).show()
                    activate()
                } catch (_: Exception) {
                    Toast.makeText(context, R.string.invalid_qr, Toast.LENGTH_LONG).show()
                }
            }
        }
    // A composição libera CameraX antes de iniciar a Activity do leitor.
    LaunchedEffect(camera, scanRequested) {
        if (scanRequested && !camera) {
            scanRequested = false
            scanner.launch(
                ScanOptions()
                    .setDesiredBarcodeFormats(ScanOptions.QR_CODE)
                    .setPrompt(context.getString(R.string.scan_prompt))
                    .setBeepEnabled(false)
                    .setBarcodeImageEnabled(false)
                    .setOrientationLocked(false),
            )
        }
    }
    LaunchedEffect(status) {
        if (status == R.string.invalid_address ||
            status == R.string.invalid_fingerprint ||
            status == R.string.invalid_token ||
            status == R.string.invalid_pairing ||
            status == R.string.connection_error ||
            status == R.string.camera_error
        ) {
            Toast.makeText(context, context.getString(status), Toast.LENGTH_LONG).show()
        }
    }
    LaunchedEffect(savedAddress) { if (address.isEmpty()) address = savedAddress }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(stringResource(R.string.app_name), style = MaterialTheme.typography.headlineLarge)
        Text(stringResource(status))
        Text(stringResource(R.string.visible_only))
        if (camera) {
            CameraPreview(front, model)
            Button(onClick = { front = !front }) { Text(stringResource(R.string.switch_camera)) }
            OutlinedButton(onClick = model::stopCamera) { Text(stringResource(R.string.stop_camera)) }
        } else {
            Button(onClick = activate) { Text(stringResource(R.string.activate_camera)) }
            Text(stringResource(R.string.camera_permission))
        }
        OutlinedButton(onClick = {
            keyboard?.hide()
            model.stopCamera()
            scanRequested = true
        }, enabled = !connecting) { Text(stringResource(R.string.scan_qr)) }
        OutlinedTextField(
            address,
            { address = it },
            label = { Text(stringResource(R.string.computer_address)) },
            singleLine = true,
            enabled = !connecting,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            fingerprint,
            { fingerprint = it },
            label = { Text(stringResource(R.string.fingerprint)) },
            enabled = !connecting,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            token,
            { token = it },
            label = { Text(stringResource(R.string.pairing_secret)) },
            visualTransformation = PasswordVisualTransformation(),
            singleLine = true,
            enabled = !connecting,
            modifier = Modifier.fillMaxWidth(),
        )
        Text(
            stringResource(status),
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.fillMaxWidth(),
        )
        if (!camera) Text(stringResource(R.string.activate_before_connect))
        Button(onClick = {
            keyboard?.hide()
            model.connect(address, fingerprint, token)
        }, enabled = camera && !connecting) {
            Text(stringResource(R.string.connect))
        }
        OutlinedButton(onClick = model::disconnect, enabled = connecting) { Text(stringResource(R.string.disconnect)) }
    }
}

@Composable
private fun CameraPreview(
    front: Boolean,
    model: StreamViewModel,
) {
    val context = LocalContext.current
    val owner = LocalLifecycleOwner.current
    val view = remember { PreviewView(context) }
    AndroidView(factory = { view }, modifier = Modifier.fillMaxWidth().height(280.dp))
    DisposableEffect(front, owner, view) {
        val camera = CameraManager(context)
        camera.start(owner, view, front, { model.connection.canSend }, model.connection::send, model::cameraError)
        onDispose { camera.stop() }
    }
}
