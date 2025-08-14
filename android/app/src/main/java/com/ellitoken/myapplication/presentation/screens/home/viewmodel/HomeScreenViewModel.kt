package com.ellitoken.myapplication.presentation.screens.home.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ellitoken.myapplication.presentation.screens.home.uistate.HomeScreenUiState
import com.ellitoken.myapplication.presentation.screens.home.uistate.VoiceState
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class HomeScreenViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(HomeScreenUiState())
    val uiState: StateFlow<HomeScreenUiState> = _uiState.asStateFlow()


    init {
        loadProfile()
    }

    private fun loadProfile() {
        _uiState.value = _uiState.value.copy(
            userName = "Yusuf Asım",
            profileImageUrl = null
        )
    }

    fun startListening() {
        // call start.
        _uiState.update { currentState ->
            currentState.copy(voiceState = VoiceState.Listening())
        }
    }


    fun stopListeningAndProcess() {
        if (_uiState.value.voiceState is VoiceState.Processing || _uiState.value.voiceState is VoiceState.Idle) return

        _uiState.update { it.copy(voiceState = VoiceState.Processing) }

        viewModelScope.launch {
            // api call.
            // Backend simülasyonu
            println("SIMULATION: Sahte API isteği başladı...")
            delay(2000) // 2 saniyelik sahte işlem süresi
            println("SIMULATION: Sahte API isteği bitti.")

            // "Speaking" durumuna geç
            _uiState.update { it.copy(voiceState = VoiceState.Speaking) }

            // AI'ın konuşmasının bittiğini simüle et
            delay(3000) // 3 saniyelik sahte konuşma süresi
            aiFinishedSpeaking()
        }
    }
    fun aiFinishedSpeaking() {
        // call when finish.
        _uiState.update { it.copy(voiceState = VoiceState.Idle) }
    }

    fun updateAmplitude(newAmplitude: Float) {
        //listening case. for animation
        _uiState.update { currentState ->
            if (currentState.voiceState is VoiceState.Listening) {
                currentState.copy(
                    voiceState = VoiceState.Listening(amplitude = newAmplitude)
                )
            } else {
                currentState
            }
        }
    }


    fun setMicClicked(clicked: Boolean) {
        _uiState.update { it.copy(isMicClicked = clicked) }
    }
}