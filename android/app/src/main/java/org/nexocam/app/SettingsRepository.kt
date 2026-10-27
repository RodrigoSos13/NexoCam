package org.nexocam.app

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.map

private val Context.settings by preferencesDataStore("nexocam")

class SettingsRepository(
    context: Context,
) {
    private val store = context.applicationContext.settings
    private val address = stringPreferencesKey("computer_address")
    val lastAddress = store.data.map { it[address] ?: "" }

    suspend fun saveAddress(value: String) {
        store.edit { it[address] = value }
    }
}
