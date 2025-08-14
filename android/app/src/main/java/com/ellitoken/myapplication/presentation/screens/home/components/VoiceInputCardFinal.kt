package com.ellitoken.myapplication.presentation.screens.home.components

import android.graphics.Color
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ellitoken.myapplication.R
import com.ellitoken.myapplication.presentation.screens.home.components.animations.ListeningAnimation
import com.ellitoken.myapplication.presentation.screens.home.components.animations.MeetStyleListeningAnimation
import com.ellitoken.myapplication.presentation.screens.home.uistate.VoiceState
import com.ellitoken.myapplication.ui.theme.appBlack

@Composable
fun VoiceInputCardFinal(
    voiceState: VoiceState,
    onMicClick: () -> Unit,
    onStopListening: () -> Unit
) {
    ElevatedCard(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp)
            .height(180.dp),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            when (voiceState) {

                is VoiceState.Idle -> {

                    Column (horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(Modifier.size(120.dp).clip(CircleShape).clickable(onClick = onMicClick)) {
                            Image(
                                painter = painterResource(id = R.drawable.homescreen_ic_voice),
                                contentDescription = "Dinlemeyi Başlat",
                                modifier = Modifier.fillMaxSize().offset(y = 8.dp)
                            )
                        }


                        Text (
                            text = "Konuşmayı Başlat",
                            color = appBlack,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Medium
                        )

                    }
                }

                is VoiceState.Listening -> {
                    Box(contentAlignment = Alignment.Center) {
                        MeetStyleListeningAnimation(
                            modifier = Modifier.size(120.dp)
                        ) {
                            Box(modifier = Modifier.size(60.dp)) // Boş content, sadece animasyon için
                        }

                        Box(
                            Modifier
                                .size(120.dp)
                                .clip(CircleShape)
                                .clickable(onClick = onStopListening)
                        ) {
                            Image(
                                painter = painterResource(id = R.drawable.homescreen_ic_voice),
                                contentDescription = "Dinlemeyi Durdur",
                                modifier = Modifier
                                    .fillMaxSize()
                                    .offset(y = 8.dp) // Aynı offset
                            )
                        }
                    }

                }
                is VoiceState.Processing -> {
                    ListeningAnimation()
                }

                is VoiceState.Speaking -> {
                    Text("AI Konuşuyor...")
                }
            }
        }
    }
}