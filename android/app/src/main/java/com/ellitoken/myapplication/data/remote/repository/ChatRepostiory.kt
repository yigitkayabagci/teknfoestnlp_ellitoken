package com.ellitoken.myapplication.data.remote.repository

import com.ellitoken.myapplication.presentation.screens.chatsupport.uistate.AiMessage
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.datetime.Clock
import java.util.UUID


class ChatSupportRepository {
    fun sendMessage(userMessage: String): Flow<AiMessage> = flow {
        delay(1000)
        emit(
            AiMessage(
                id = UUID.randomUUID().toString(),
                createdAt = Clock.System.now(),
                message = "Merhaba! Mesajını aldım: \"$userMessage\"",
                fromAi = true
            )
        )
        delay(1500)
        emit(
            AiMessage(
                id = UUID.randomUUID().toString(),
                createdAt = Clock.System.now(),
                message = "Size nasıl yardımcı olabilirim?",
                fromAi = true
            )
        )
    }
}