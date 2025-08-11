package com.ellitoken.myapplication.di

import com.ellitoken.myapplication.presentation.screens.calendar.viewmodel.CalendarScreenViewModel
import com.ellitoken.myapplication.presentation.screens.chatsupport.viewmodel.ChatSupportScreenViewModel
import com.ellitoken.myapplication.presentation.screens.home.viewmodel.HomeScreenViewModel
import com.ellitoken.myapplication.presentation.screens.profile.viewmodel.ProfileScreenViewModel
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

val appModule = module {

    single { HomeScreenViewModel() }
    viewModel{ CalendarScreenViewModel() }
    viewModel{ ChatSupportScreenViewModel() }
    viewModel{ ProfileScreenViewModel() }

}