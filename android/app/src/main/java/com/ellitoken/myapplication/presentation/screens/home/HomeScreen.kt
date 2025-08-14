package com.ellitoken.myapplication.presentation.screens.home

import android.Manifest
import android.content.pm.PackageManager
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavController
import androidx.navigation.NavGraph.Companion.findStartDestination
import com.ellitoken.myapplication.R
import com.ellitoken.myapplication.data.remote.model.upcomingAppointments
import com.ellitoken.myapplication.presentation.navigation.Screen
import com.ellitoken.myapplication.presentation.screens.home.components.*
import com.ellitoken.myapplication.presentation.screens.home.viewmodel.HomeScreenViewModel
import com.ellitoken.myapplication.ui.theme.appBackground
import org.koin.androidx.compose.getViewModel

@Composable
fun HomeScreen(
    navController: NavController,
    viewModel: HomeScreenViewModel = getViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current

    val blurRadius by animateDpAsState(
        targetValue = if (uiState.isMicClicked) 16.dp else 0.dp,
        label = "blur"
    )

    // Tek launcher: RECORD_AUDIO izni için
    val micPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            viewModel.startListening()
        } else {
            Toast.makeText(context, "Mikrofon izni gerekli", Toast.LENGTH_SHORT).show()
        }
    }

    // Ortak fonksiyon: izin var mı? varsa başlat, yoksa iste
    fun requestMicAndStart() {
        val granted = ContextCompat.checkSelfPermission(
            context, Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED

        if (granted) {
            viewModel.startListening()
        } else {
            micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    Scaffold(
        topBar = {
            HomeScreenTopBar(
                modifier = Modifier.blur(blurRadius),
                userName = uiState.userName,
                profileImageUrl = uiState.profileImageUrl,
                onClickProfile = {
                    navController.navigate(Screen.ProfileScreen.route) {
                        popUpTo(navController.graph.findStartDestination().id) {
                            saveState = true
                        }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(appBackground)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(Modifier.height(24.dp))

            VoiceInputCardFinal(
                isSpeaking = uiState.isSpeaking,
                setSpeaking = viewModel::setSpeaking,
                voiceState = uiState.voiceState,
                onMicClick = {
                    viewModel.setMicClicked(true)
                    requestMicAndStart()
                },
                onStopListening = {
                    viewModel.stopListeningAndProcess()
                }
            )

            Spacer(Modifier.height(24.dp))

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .blur(blurRadius)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 24.dp),
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                        HomePageInfo(
                            iconRes = R.drawable.homepageinfo_calendar,
                            title = "Yaklaşan Randevular",
                            description = "2 randevu",
                            onClick = { },
                            outerPadding = 0.dp,
                            modifier = Modifier.weight(1f)
                        )
                        HomePageInfo(
                            iconRes = R.drawable.homepageinfo_health,
                            title = "Sağlık Durumu",
                            description = "Son kontrol",
                            onClick = { },
                            outerPadding = 0.dp,
                            modifier = Modifier.weight(1f)
                        )
                    }

                    Spacer(Modifier.height(16.dp))

                    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                        HomePageInfo(
                            iconRes = R.drawable.homepageinfo_calendar,
                            title = "İlaçlarım",
                            description = "3 aktif",
                            onClick = { },
                            outerPadding = 0.dp,
                            modifier = Modifier.weight(1f)
                        )
                        HomePageInfo(
                            iconRes = R.drawable.homepageinfo_health,
                            title = "Tahliller",
                            description = "2 yeni sonuç",
                            onClick = { },
                            outerPadding = 0.dp,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }

                Spacer(Modifier.height(16.dp))

                UpcomingAppointmentsSection(
                    appointments = upcomingAppointments,
                    onAppointmentClick = { }
                )

                Spacer(Modifier.height(24.dp))
            }
        }
    }
}
