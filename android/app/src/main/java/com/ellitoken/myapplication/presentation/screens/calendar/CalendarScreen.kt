package com.ellitoken.myapplication.presentation.screens.calendar

import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController

@Composable
fun CalendarScreen(navController: NavController) {
    Text(
        text = "Calendar",
        fontWeight = FontWeight.Bold,
        fontSize = 20.sp
    )
}