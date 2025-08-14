package com.ellitoken.myapplication.presentation.screens.home.uistate

data class HomeScreenUiState(
    val isLoading: Boolean = false,
    val userName: String = "",
    val profileImageUrl: String? = null,
    val voiceState: VoiceState = VoiceState.Idle,
    val isMicClicked: Boolean = false,
    val isSpeaking: Boolean = false
)

sealed class VoiceState {
    object Idle : VoiceState()
    data class Listening(var amplitude: Float = 0f) : VoiceState()
    object Processing : VoiceState()
    object Speaking : VoiceState()
}
