package com.ellitoken.myapplication.presentation.screens.home.viewmodel

import android.Manifest
import android.util.Log
import androidx.annotation.RequiresPermission
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ellitoken.myapplication.presentation.screens.home.uistate.*
import com.ellitoken.myapplication.data.domain.VoiceRecorder
import com.ellitoken.myapplication.data.remote.api.VoiceApiService
import com.ellitoken.myapplication.data.remote.model.User
import com.ellitoken.myapplication.repository.UserRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.io.File

data class HealthSurveyItem(
    val key: String,
    val question: String,
    val isChecked: Boolean,
    val description: String
)

class HomeScreenViewModel(
    private val userRepository: UserRepository,
    private val recorder: VoiceRecorder,
    private val voiceApiService: VoiceApiService
) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeScreenUiState())
    val uiState: StateFlow<HomeScreenUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            val mockUser = User(
                id = "111111111",
                imageUrl = "https://randomuser.me/api/portraits/men/1.jpg",
                fullName = "Yusuf Asım Demirhan",
                dateOfBirth = "15/06/1990",
                gender = "Male",
                email = "ahmet.yilmaz@example.com",

                hasChronicIllness = true,
                chronicIllnessDescription = "Hipertansiyon ve hafif astım",

                hadSurgeries = true,
                surgeriesDescription = "2015 yılında apandisit ameliyatı",

                takingRegularMedications = true,
                medicationsDescription = "Tansiyon ilacı ve vitamin takviyesi",

                smokes = false,
                smokingDescription = "",

                drinksAlcohol = true,
                alcoholDescription = "Sosyal ortamlarda ara sıra",

                hasAllergies = true,
                allergiesDescription = "Fıstık ve polen alerjisi"
            )

            _uiState.update {
                it.copy(
                    isLoading = false,
                    user = mockUser
                )
            }
        }

        recorder.onListeningStarted = {
            _uiState.update { it.copy(voiceState = VoiceState.Listening()) }
        }
        recorder.onEndpointDetected = {
            val recordedFile = recorder.getLastRecordedFile()

            if (recordedFile != null && recordedFile.exists()) {
                processRecordedAudio(recordedFile)
            } else {
                _uiState.update {
                    it.copy(
                        voiceState = VoiceState.Idle,
                        isMicClicked = false
                    )
                }
            }
        }


        recorder.onError = { errorMessage, throwable ->
            _uiState.update {
                it.copy(
                    voiceState = VoiceState.Idle,
                    isMicClicked = false,
                    isSpeaking = false
                )
            }
        }


    }

    fun updateHealthInfo(key: String, isChecked: Boolean, description: String) {
        _uiState.update { state ->
            val user = state.user ?: return@update state

            val finalDescription = if (isChecked) description else ""

            val updatedUser = when (key) {
                "chronicIllness" -> user.copy(hasChronicIllness = isChecked, chronicIllnessDescription = finalDescription)
                "surgeries" -> user.copy(hadSurgeries = isChecked, surgeriesDescription = finalDescription)
                "medications" -> user.copy(takingRegularMedications = isChecked, medicationsDescription = finalDescription)
                "smokes" -> user.copy(smokes = isChecked, smokingDescription = finalDescription)
                "alcohol" -> user.copy(drinksAlcohol = isChecked, alcoholDescription = finalDescription)
                "allergies" -> user.copy(hasAllergies = isChecked, allergiesDescription = finalDescription)
                else -> user
            }
            state.copy(user = updatedUser)
        }
    }

    fun getHealthSurveyItems(): List<HealthSurveyItem> {
        val user = _uiState.value.user ?: return emptyList()
        return listOf(
            HealthSurveyItem("chronicIllness", "Kronik bir hastalığınız var mı?", user.hasChronicIllness, user.chronicIllnessDescription),
            HealthSurveyItem("surgeries", "Daha önce ameliyat geçirdiniz mi?", user.hadSurgeries, user.surgeriesDescription),
            HealthSurveyItem("medications", "Düzenli ilaç kullanıyor musunuz?", user.takingRegularMedications, user.medicationsDescription),
            HealthSurveyItem("smokes", "Sigara kullanıyor musunuz?", user.smokes, user.smokingDescription),
            HealthSurveyItem("alcohol", "Alkol kullanıyor musunuz?", user.drinksAlcohol, user.alcoholDescription),
            HealthSurveyItem("allergies", "Bilinen bir alerjiniz var mı?", user.hasAllergies, user.allergiesDescription)
        )
    }

    fun openHealthSurveySheet() {
        _uiState.update { it.copy(isHealthSurveySheetOpen = true) }
    }

    fun closeHealthSurveySheet() {
        _uiState.update { it.copy(isHealthSurveySheetOpen = false) }
    }

    private fun processRecordedAudio(audioFile: File) {
        viewModelScope.launch {
            _uiState.update { it.copy(voiceState = VoiceState.Processing) }
            val resultFile = voiceApiService.processAudioAndGetResult(audioFile)

            if (resultFile != null) {
                _uiState.update {
                    it.copy(
                        voiceState = VoiceState.Speaking,
                        isSpeaking = true,
                        processedAudioFile = resultFile
                    )
                }
            } else {
                _uiState.update {
                    it.copy(
                        voiceState = VoiceState.Idle,
                        isMicClicked = false
                    )
                }
            }
        }
    }

    fun onPlaybackFinished() {
        _uiState.value.processedAudioFile?.delete()

        viewModelScope.launch {
            delay(500)
            Log.d("HomeScreenViewModel", "onPlaybackFinished")
            _uiState.update {
                it.copy(
                    isSpeaking = false,
                    processedAudioFile = null,
                    voiceState = VoiceState.Listening(),
                    isMicClicked = true
                )
            }

            // Fiziksel olarak kaydı yeniden başlat
            recorder.startRecording()
        }
    }

    @RequiresPermission(Manifest.permission.RECORD_AUDIO)
    fun startListening() {
        _uiState.update { it.copy(voiceState = VoiceState.Listening(), isMicClicked = true) }
        recorder.startRecording()
    }

    fun stopListeningAndProcess() {
        recorder.forceStopAndSend()
    }

    fun setMicClicked(clicked: Boolean) {
        _uiState.update { it.copy(isMicClicked = clicked) }
    }

    fun setSpeaking(value: Boolean) {
        _uiState.update { it.copy(isSpeaking = value) }
    }

    fun changeStateToIdle() {
        _uiState.update {
            it.copy(
                voiceState = VoiceState.Idle,
                isMicClicked = false,
                isSpeaking = false
            )
        }
    }

    fun stopAutoCycle() {
        recorder.forceStopAndSend()
        changeStateToIdle()
    }

    override fun onCleared() {
        super.onCleared()
    }

}