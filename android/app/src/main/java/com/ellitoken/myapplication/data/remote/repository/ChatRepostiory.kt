package com.ellitoken.myapplication.data.remote.repository

import com.ellitoken.myapplication.presentation.screens.chatsupport.uistate.AiMessage
import io.ktor.client.HttpClient
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.datetime.Clock
import java.util.UUID


    import io.ktor.client.*
    import io.ktor.client.engine.android.*
    import io.ktor.client.plugins.contentnegotiation.*
    import io.ktor.client.request.*
    import io.ktor.client.statement.*
    import io.ktor.serialization.kotlinx.json.*
    import kotlinx.coroutines.delay

    class ChatSupportRepository() {
        // API adresi ve endpoint'i
        // private val apiUrl = "https://api.example.com/chat"

//        private val httpClient = HttpClient(Android) {
//            install(ContentNegotiation) {
//                json(Json {
//                    ignoreUnknownKeys = true
//                    isLenient = true
//                })
//            }
//        }


        fun sendMessage(userMessage: String): Flow<AiMessage> = flow {
            delay(1000)

            // *** Burası API isteği atılacak kısım ***
            //
            // val response = httpClient.post(apiUrl) {
            //     headers {
            //         append("Content-Type", "application/json")
            //         append("Authorization", "Bearer YOUR_API_KEY")
            //     }
            //     setBody(mapOf("prompt" to userMessage))
            // }
            //
            // val responseBody = response.bodyAsText()
            //
            // val aiResponse = AiMessage(
            //     id = UUID.randomUUID().toString(),
            //     createdAt = Clock.System.now(),
            //     message = responseBody, // API'den gelen mesaj
            //     fromAi = true
            // )
            //
            // emit(aiResponse)
            // *** API isteği atılacak kısım sonu ***


            // Geçici olarak statik mesajları döndürmeye devam edelim.
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