package com.ellitoken.myapplication.data.remote.api
import android.os.Environment
import io.ktor.client.*
import io.ktor.client.engine.cio.CIO
import io.ktor.client.request.*
import io.ktor.client.request.forms.formData
import io.ktor.client.request.forms.submitFormWithBinaryData
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.utils.io.jvm.javaio.*
import kotlinx.coroutines.delay
import java.io.File
import java.io.FileOutputStream
import android.content.Context
import com.ellitoken.myapplication.R


class VoiceApiService(private val context: Context) {



    suspend fun processAudioAndGetResult(audioFile: File): File? {
        return try {
            println("--- LOKAL TEST MODU AKTİF ---")

            // 1. Ağ isteği gecikmesini simüle et
            println("-> API gecikmesi simüle ediliyor...")
            delay(2000) // 2 saniye bekle

            // 2. Kullanıcının kaydettiği sesi kontrol için Downloads'a kaydet
            saveInputForDebugging(audioFile)

            // 3. API'den gelmiş gibi bir cevap dosyası oluştur ve döndür
            println("-> Test yanıtı oluşturuluyor...")
            createDummyResponseFile()

        } catch (e: Exception) {
            println("Lokal test sırasında hata: ${e.message}")
            null
        }
    }

    /**
     * Gelen ses kaydını (kullanıcının konuşmasını) Downloads klasörüne kopyalar.
     */
    private fun saveInputForDebugging(inputFile: File) {
        val downloadDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
        if (!downloadDir.exists()) {
            downloadDir.mkdirs()
        }
        val timestamp = System.currentTimeMillis()
        val debugFile = File(downloadDir, "recorded_input_${timestamp}.3gp")
        inputFile.copyTo(debugFile, overwrite = true)
        println("-> Gelen kayıt Downloads klasörüne kopyalandı: ${debugFile.name}")
    }

    /**
     * res/raw klasöründeki test ses dosyasını geçici bir dosyaya kopyalayarak
     * API'den dönmüş gibi davranmasını sağlar.
     */
    private fun createDummyResponseFile(): File? {
        val inputStream = context.resources.openRawResource(R.raw.test_deneme)
        val responseFile = File.createTempFile("api_response_", ".mp3", context.cacheDir)
        val outputStream = FileOutputStream(responseFile)
        inputStream.copyTo(outputStream)
        outputStream.close()
        inputStream.close()
        println("-> Cevap dosyası oluşturuldu: ${responseFile.absolutePath}")
        return responseFile
    }

    /*
    suspend fun processAudioAndGetResult(audioFile: File): File? {
        val client = HttpClient(CIO)
        val url = "http://api_adresiniz/ses_isleme_uc_noktasi"
        val outputFile = File("processed_audio.wav")

        return try {
            val response: HttpResponse = client.submitFormWithBinaryData(
                url = url,
                formData = formData {
                    append("audio_file", audioFile.readBytes(), Headers.build {
                        append(HttpHeaders.ContentType, "audio/wav")
                        append(HttpHeaders.ContentDisposition, "filename=\"${audioFile.name}\"")
                    })
                }
            )

            if (response.status.isSuccess()) {
                println("Ses dosyası başarıyla işlendi. Yanıt alınıyor...")

                response.bodyAsChannel().copyTo(FileOutputStream(outputFile))

                println("İşlenmiş ses dosyası başarıyla kaydedildi: ${outputFile.absolutePath}")
                outputFile
            } else {
                println("Hata: İşlem sırasında bir sorun oluştu. Durum kodu: ${response.status}")
                null
            }
        } catch (e: Exception) {
            println("Ağ hatası: ${e.message}")
            null
        } finally {
            client.close()
        }
    }*/



}