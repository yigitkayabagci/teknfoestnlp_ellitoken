package com.ellitoken.myapplication.presentation.screens.chatsupport.uistate

import androidx.compose.ui.text.input.TextFieldValue
import kotlinx.serialization.Serializable

data class ChatSupportScreenUiState(
    val messages: List<AiMessage> = emptyList(),
    val textFieldValue: TextFieldValue = TextFieldValue(),
    val isLoading: Boolean = false
)

@Serializable
data class AiMessage(
    val id: String,
    val createdAt: kotlinx.datetime.Instant,
    val message: String,
    val fromAi: Boolean = true
)
