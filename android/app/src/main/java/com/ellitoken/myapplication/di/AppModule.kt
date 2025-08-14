package com.ellitoken.myapplication.di

import com.ellitoken.myapplication.data.domain.VoiceRecorder
import com.ellitoken.myapplication.data.remote.repository.ChatSupportRepository
import com.ellitoken.myapplication.presentation.screens.calendar.viewmodel.CalendarScreenViewModel
import com.ellitoken.myapplication.presentation.screens.chatsupport.viewmodel.ChatSupportScreenViewModel
import com.ellitoken.myapplication.presentation.screens.home.viewmodel.HomeScreenViewModel
import com.ellitoken.myapplication.presentation.screens.profile.viewmodel.ProfileScreenViewModel
import org.koin.android.ext.koin.androidContext
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

val appModule = module {
    single { ChatSupportRepository() }
    factory { VoiceRecorder(androidContext()) }
    single { HomeScreenViewModel(get()) }

    viewModel{ CalendarScreenViewModel() }
    viewModel{ ChatSupportScreenViewModel(get()) }
    viewModel{ ProfileScreenViewModel() }

}