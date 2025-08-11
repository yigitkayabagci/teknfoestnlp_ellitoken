package com.ellitoken.myapplication.presentation.screens.chatsupport

import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController

@Composable
fun ChatSupportScreen(navController: NavController) {
    Text(
        text = "Chat",
        fontWeight = FontWeight.Bold,
        fontSize = 20.sp
    )
}