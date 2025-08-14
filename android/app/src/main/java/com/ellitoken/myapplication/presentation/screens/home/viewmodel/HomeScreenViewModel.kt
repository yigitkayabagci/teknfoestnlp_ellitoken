package com.ellitoken.myapplication.presentation.screens.home.viewmodel

import android.Manifest
import androidx.annotation.RequiresPermission
import androidx.lifecycle.ViewModel
import com.ellitoken.myapplication.presentation.screens.home.uistate.*
import com.ellitoken.myapplication.data.domain.VoiceRecorder
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

// HomeScreenViewModel.kt
class HomeScreenViewModel(
    private val recorder: VoiceRecorder
) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeScreenUiState())
    val uiState: StateFlow<HomeScreenUiState> = _uiState.asStateFlow()

    init {
        _uiState.update { it.copy(userName = "Yusuf Asım", profileImageUrl = null) }

        // VoiceRecorder callback'leri
        recorder.onListeningStarted = {
            _uiState.update { it.copy(voiceState = VoiceState.Listening()) }
        }
        recorder.onEndpointDetected = {
            _uiState.update { it.copy(voiceState = VoiceState.Processing) }
        }
        recorder.onUploadingStarted = {
            _uiState.update { it.copy(voiceState = VoiceState.Processing) }
        }
        recorder.onPlaybackStarted = {
            _uiState.update { it.copy(voiceState = VoiceState.Speaking) }
        }
        recorder.onPlaybackCompleted = {
            _uiState.update { it.copy(voiceState = VoiceState.Idle, isMicClicked = false) }
            // İstersen burada otomatik tekrar dinlemeye al:
            // startListening()
        }
        recorder.onError = { _, _ ->
            _uiState.update { it.copy(voiceState = VoiceState.Idle, isMicClicked = false) }
        }
    }

    @RequiresPermission(Manifest.permission.RECORD_AUDIO)
    fun startListening() {
        _uiState.update { it.copy(voiceState = VoiceState.Listening(), isMicClicked = true) }
        recorder.startRecording()
    }

    fun stopListeningAndProcess() {
        recorder.forceStopAndSend()
        // Sonraki geçişleri callback'ler yapacak (Processing → Speaking → Idle)
    }

    fun setMicClicked(clicked: Boolean) {
        _uiState.update { it.copy(isMicClicked = clicked) }
    }

    override fun onCleared() {
        super.onCleared()
        // recorder.release() gibi bir şeyin varsa burada çağır
    }
}
