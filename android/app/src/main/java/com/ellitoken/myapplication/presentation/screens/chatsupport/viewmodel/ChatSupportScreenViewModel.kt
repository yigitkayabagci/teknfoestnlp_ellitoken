package com.ellitoken.myapplication.presentation.screens.chatsupport.viewmodel

import androidx.compose.ui.text.input.TextFieldValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ellitoken.myapplication.data.remote.repository.ChatSupportRepository
import com.ellitoken.myapplication.presentation.screens.chatsupport.uistate.AiMessage
import com.ellitoken.myapplication.presentation.screens.chatsupport.uistate.ChatSupportScreenUiState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.datetime.Clock
import java.util.UUID

class ChatSupportScreenViewModel(
    private val repository: ChatSupportRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatSupportScreenUiState())
    val uiState = _uiState.asStateFlow()

    fun onTextValueChanged(value: TextFieldValue) {
        _uiState.update { it.copy(textFieldValue = value) }
    }

    fun sendMessage() {
        val text = uiState.value.textFieldValue.text
        if (text.isBlank()) return

        val userMessage = AiMessage(
            id = UUID.randomUUID().toString(),
            createdAt = Clock.System.now(),
            message = text,
            fromAi = false
        )

        _uiState.update {
            it.copy(
                messages = listOf(userMessage) + it.messages,
                textFieldValue = TextFieldValue(),
                isLoading = true
            )
        }

        viewModelScope.launch {
            repository.sendMessage(text).collect { aiMessage ->
                _uiState.update {
                    it.copy(messages = listOf(aiMessage) + it.messages, isLoading = false)
                }
            }
        }
    }
}