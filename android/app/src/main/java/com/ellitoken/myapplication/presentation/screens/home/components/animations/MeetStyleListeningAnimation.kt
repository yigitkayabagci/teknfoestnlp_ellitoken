package com.ellitoken.myapplication.presentation.screens.home.components.animations

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp

/**
 * Google Meet tarzı, ortasında bir içerik olan ve etrafında halkalar yayan animasyon.
 *
 * @param modifier Bu animasyonun ve içeriğinin kaplayacağı alanı belirler.
 * @param circleColor Yayılan halkaların rengi.
 * @param content Ortada gösterilecek olan Composable (örneğin bir Icon veya IconButton).
 */
@Composable
fun MeetStyleListeningAnimation(
    modifier: Modifier = Modifier,
    circleColor: Color = MaterialTheme.colorScheme.primary,
    content: @Composable () -> Unit
) {
    val infiniteTransition = rememberInfiniteTransition("meet-style-transition")

    // 3 adet halka oluşturacağız. Her biri için 2 animasyon: boyut (scale) ve görünürlük (alpha).
    val animatedProperties = List(3) { index ->
        // Boyut animasyonu: 1x'ten 2x'e kadar büyüyecek (3.5f yerine 2.0f)
        val scale by infiniteTransition.animateFloat(
            initialValue = 1f,
            targetValue = 2.0f, // BURASI DEĞİŞTİ: 3.5f → 2.0f
            animationSpec = infiniteRepeatable(
                animation = tween(2000, easing = LinearEasing),
                repeatMode = RepeatMode.Restart,
                initialStartOffset = StartOffset(index * 700) // Her halka 700ms arayla başlasın
            ),
            label = "scale_$index"
        )
        // Alfa animasyonu: Başta opak, sona doğru tamamen şeffaf olacak.
        val alpha by infiniteTransition.animateFloat(
            initialValue = 1f,
            targetValue = 0f,
            animationSpec = infiniteRepeatable(
                animation = tween(2000, easing = LinearEasing),
                repeatMode = RepeatMode.Restart,
                initialStartOffset = StartOffset(index * 700)
            ),
            label = "alpha_$index"
        )
        scale to alpha
    }

    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center
    ) {
        // 1. Arka Plan: Genişleyen halkaları çiz
        Canvas(modifier = Modifier.fillMaxSize()) {
            val baseRadius = size.minDimension / 2.0f

            animatedProperties.forEach { (scale, alpha) ->
                drawCircle(
                    color = circleColor.copy(alpha = alpha),
                    radius = baseRadius * scale,
                    style = Stroke(width = 2.dp.toPx()) // İçi boş daire için Stroke kullan
                )
            }
        }
        // 2. Ön Plan: Ortadaki asıl içeriği (ikonu) göster
        content()
    }
}