package org.nexocam.app

import okhttp3.Dns
import okhttp3.OkHttpClient
import java.net.InetAddress
import java.security.MessageDigest
import java.security.cert.CertificateException
import java.security.cert.X509Certificate
import java.util.Locale
import java.util.concurrent.TimeUnit
import javax.net.ssl.SSLContext
import javax.net.ssl.X509TrustManager

enum class PairingField { ADDRESS, FINGERPRINT, TOKEN }

class InvalidPairing(
    val field: PairingField,
) : IllegalArgumentException()

data class Pairing(
    val address: String,
    val fingerprint: String,
    val token: String,
) {
    override fun toString() = "Pairing(address=$address, credentials=redacted)"

    init {
        val parts = address.split('.')
        if (!(
                parts.size == 4 &&
                    parts.all {
                        it.isNotEmpty() && it.all(Char::isDigit) && it.length <= 3 && (it.toIntOrNull() ?: -1) in 0..255
                    }
            )
        ) {
            throw InvalidPairing(PairingField.ADDRESS)
        }
        if (!fingerprint.matches(Regex("[0-9a-fA-F]{64}"))) throw InvalidPairing(PairingField.FINGERPRINT)
        if (!token.matches(Regex("[0-9a-f]{64}"))) throw InvalidPairing(PairingField.TOKEN)
    }
}

fun parsePairing(
    address: String,
    fingerprint: String,
    token: String,
): Pairing =
    Pairing(
        address.trim(),
        fingerprint.filterNot(Char::isWhitespace).replace(":", "").lowercase(Locale.ROOT),
        token.filterNot(Char::isWhitespace).lowercase(Locale.ROOT),
    )

class PinnedTrustManager(
    private val fingerprint: String,
) : X509TrustManager {
    override fun getAcceptedIssuers(): Array<X509Certificate> = emptyArray()

    override fun checkClientTrusted(
        chain: Array<X509Certificate>,
        authType: String,
    ): Unit = throw CertificateException("Certificado de cliente não utilizado")

    override fun checkServerTrusted(
        chain: Array<X509Certificate>,
        authType: String,
    ) {
        if (chain.isEmpty()) throw CertificateException("Certificado ausente")
        val actual = MessageDigest.getInstance("SHA-256").digest(chain[0].encoded)
        val expected = fingerprint.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
        if (!MessageDigest.isEqual(actual, expected)) throw CertificateException("Identidade diferente")
        chain[0].checkValidity()
    }
}

fun pinnedClient(pairing: Pairing): OkHttpClient {
    val trust = PinnedTrustManager(pairing.fingerprint)
    val tls = SSLContext.getInstance("TLS").apply { init(null, arrayOf(trust), null) }
    return OkHttpClient
        .Builder()
        .sslSocketFactory(tls.socketFactory, trust)
        // O nome TLS permanece fixo e validado pelo verificador padrão do OkHttp.
        // Só o destino TCP varia; nenhum hostnameVerifier permissivo é instalado.
        .dns(
            object : Dns {
                override fun lookup(hostname: String): List<InetAddress> {
                    require(hostname == "nexocam.local")
                    return listOf(InetAddress.getByName(pairing.address))
                }
            },
        ).proxy(java.net.Proxy.NO_PROXY)
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(25, TimeUnit.SECONDS)
        .pingInterval(10, TimeUnit.SECONDS)
        .retryOnConnectionFailure(false)
        .followRedirects(false)
        .followSslRedirects(false)
        .build()
}
