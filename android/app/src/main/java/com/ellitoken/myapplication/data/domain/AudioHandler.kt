//package com.ellitoken.myapplication.voice
//
//import android.Manifest
//import android.annotation.SuppressLint
//import android.content.Context
//import android.media.*
//import android.os.Build
//import android.util.Log
//import androidx.annotation.RequiresPermission
//import kotlinx.coroutines.*
//import kotlinx.coroutines.flow.*
//import okhttp3.*
//import okio.ByteString
//import com.konovalov.vad.silero.*
//import com.konovalov.vad.silero.config.FrameSize
//import com.konovalov.vad.silero.config.Mode
//import com.konovalov.vad.silero.config.SampleRate
//import io.github.jaredmdobson.concentus.OpusApplication
//import io.github.jaredmdobson.concentus.OpusEncoder
//import io.github.jaredmdobson.concentus.OpusSignal
//import java.nio.ByteBuffer
//import java.nio.ByteOrder
//import kotlin.math.max
//
//data class AudioCfg(
//    val sampleRate: Int = 16000,
//    val channelMask: Int = AudioFormat.CHANNEL_IN_MONO,
//    val encoding: Int = AudioFormat.ENCODING_PCM_16BIT,
//    val frameMs: Int = 20,                   // 20ms @16k → 320 örnek
//) {
//    val frameSamples = (sampleRate * frameMs) / 1000
//    val frameBytes = frameSamples * 2        // PCM16 mono
//}
//
//@RequiresPermission(Manifest.permission.RECORD_AUDIO)
//private fun createAudioRecordSafe(cfg: AudioCfg, context: Context): AudioRecord {
//    val sources = intArrayOf(
//        MediaRecorder.AudioSource.VOICE_RECOGNITION,
//        MediaRecorder.AudioSource.MIC,
//        MediaRecorder.AudioSource.VOICE_COMMUNICATION,
//        MediaRecorder.AudioSource.DEFAULT,
//        MediaRecorder.AudioSource.CAMCORDER
//    )
//    val rates = intArrayOf(cfg.sampleRate, 16000, 48000, 44100, 8000) // fallback sırasi
//    val channel = cfg.channelMask
//    val encoding = cfg.encoding
//
//    var lastErr: Throwable? = null
//
//    for (src in sources) {
//        for (sr in rates) {
//            val min = AudioRecord.getMinBufferSize(sr, channel, encoding)
//
//            if (min <= 0) continue
//            try {
//                val ar = AudioRecord.Builder()
//                    .setAudioSource(src)
//                    .setAudioFormat(
//                        AudioFormat.Builder()
//                            .setSampleRate(sr)
//                            .setChannelMask(channel)
//                            .setEncoding(encoding)
//                            .build()
//                    )
//                    .setBufferSizeInBytes(max(min, cfg.frameBytes * 8))
//                    .build()
//
//                if (ar.state == AudioRecord.STATE_INITIALIZED) {
//                    // Yerleşik mikrofona zorla (BT’yi atla)
//                    try {
//                        if (Build.VERSION.SDK_INT >= 23) {
//                            val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
//                            val builtin = am.getDevices(AudioManager.GET_DEVICES_INPUTS)
//                                .firstOrNull { it.type == AudioDeviceInfo.TYPE_BUILTIN_MIC }
//                            if (builtin != null) ar.preferredDevice = builtin
//                        }
//                        // SCO açık ise kapat
//                        val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
//                        if (am.isBluetoothScoOn) {
//                            am.stopBluetoothSco(); am.isBluetoothScoOn = false
//                        }
//                    } catch (_: Throwable) { /* cihaz desteklemeyebilir */ }
//
//                    return ar
//                } else {
//                    ar.release()
//                }
//            } catch (t: Throwable) {
//                lastErr = t
//            }
//        }
//    }
//    throw UnsupportedOperationException("AudioRecord couldn't be created with any combination", lastErr)
//}
//
///** Mikrofonu 20ms PCM16 kareleri olarak yayınlar */
//class MicReader(
//    private val cfg: AudioCfg,
//    private val appContext: Context
//) {
//    private var rec: AudioRecord? = null
//
//    @androidx.annotation.RequiresPermission(android.Manifest.permission.RECORD_AUDIO)
//    fun start(): Flow<ByteArray> = flow {
//        val ar = createAudioRecordSafe(cfg, appContext)
//        rec = ar
//        ar.startRecording()
//
//        val buf = ByteArray(cfg.frameBytes)
//        while (currentCoroutineContext().isActive) {
//            val read = ar.read(buf, 0, buf.size)
//            if (read > 0) emit(buf.copyOf(read))
//        }
//    }.flowOn(Dispatchers.IO)
//
//    fun stop() {
//        rec?.run { try { stop() } catch (_: Throwable) {}; release() }
//        rec = null
//    }
//}
//
///** Silero VAD adaptörü: 20ms kareleri 512-örnek pencerelere kayan şekilde değerlendirir */
//private class SileroVadAdapter(
//    context: Context,
//    endSilenceMs: Int = 700
//) {
//    private val vad = VadSilero(
//        context,
//        sampleRate = SampleRate.SAMPLE_RATE_16K,
//        frameSize  = FrameSize.FRAME_SIZE_512,   // 512/1024/1536 @ 16k desteklenir
//        mode       = Mode.NORMAL,
//        silenceDurationMs = 300,
//        speechDurationMs = 50
//    )
//    private val windowBytes = 512 * 2
//    private val windowMs = (512 * 1000) / 16000
//    private val acc = java.io.ByteArrayOutputStream()
//    private var silenceAccum = 0
//    private val endThresh = endSilenceMs
//
//    fun pushAndIsEndpoint(framePcm16: ByteArray): Boolean {
//        acc.write(framePcm16)
//        while (acc.size() >= windowBytes) {
//            val all = acc.toByteArray()
//            val winBytes = all.copyOfRange(0, windowBytes)
//            val hop = framePcm16.size.coerceAtMost(windowBytes)
//            val remain = all.copyOfRange(hop, all.size)
//            acc.reset(); acc.write(remain)
//
//            val winShorts = pcm16leBytesToShorts(winBytes)
//            val speech = vad.isSpeech(winShorts)
//
//            if (speech) {
//                silenceAccum = 0
//            } else {
//                silenceAccum += windowMs
//                if (silenceAccum >= endThresh) return true
//            }
//        }
//        return false
//    }
//
//    fun reset() { silenceAccum = 0; acc.reset() }
//    fun close() = vad.close()
//}
//
//
//
//
//
///*
///** Opus encoder (concentus) */
//private class OpusEncoder16k(frameSamples: Int) {
//    private val enc = OpusEncoder(
//        16000,            // 16000
//        1,              // 1
//        OpusApplication.OPUS_APPLICATION_VOIP
//    ).apply {
//        setBitrate(16_000)                                      // bps
//        setSignalType(org.concentus.OpusSignal.OPUS_SIGNAL_VOICE)
//        setComplexity(5)                                        // 0..10
//        setInbandFEC(false)                                     // 0 -> false
//        setDtx(true)
//    }
//    private val tmpShort = ShortArray(frameSamples)
//    fun encode(pcm16: ByteArray): ByteArray {
//        ByteBuffer.wrap(pcm16).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().get(tmpShort)
//        val out = ByteArray(400)
//        val len = enc.encode(tmpShort, 0, tmpShort.size, out, 0, out.size)
//        return out.copyOf(len)
//    }
//}
///*
//
//
// */
// */
//
//private fun pcm16leBytesToShorts(bytes: ByteArray): ShortArray {
//    val out = ShortArray(bytes.size / 2)
//    ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().get(out)
//    return out
//}
//
//
///** OkHttp WebSocket client (echo ile test) */
//private class WsClient(
//    url: String,
//    headers: Map<String,String> = emptyMap(),
//    private val onBinary: (ByteArray)->Unit,
//    private val onOpen: ()->Unit,
//    private val onFail: (Throwable)->Unit
//) : WebSocketListener() {
//    private val client = OkHttpClient() // genelde tek instance paylaşmak iyidir. :contentReference[oaicite:2]{index=2}
//    private var ws: WebSocket? = null
//    init {
//        val req = Request.Builder().url(url).apply { headers.forEach { (k,v) -> addHeader(k,v) } }.build()
//        ws = client.newWebSocket(req, this) // OkHttp’nin WebSocket API’si. :contentReference[oaicite:3]{index=3}
//    }
//    fun sendBinary(b: ByteArray) { ws?.send(ByteString.of(*b)) }
//    fun sendText(t: String) { ws?.send(t) }
//    fun close() { ws?.close(1000,"bye"); client.dispatcher.executorService.shutdown() }
//    override fun onOpen(webSocket: WebSocket, response: Response) = onOpen()
//    override fun onMessage(webSocket: WebSocket, bytes: ByteString) = onBinary(bytes.toByteArray())
//    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) = onFail(t)
//}
//
///** DI gerektirmeyen küçük motor */
//class VoiceEngine(
//    private val appContext: Context,
//    private val serverUrl: String = "wss://echo.websocket.events/" // public echo
//) {
//    private val cfg = AudioCfg()
//    private val mic = MicReader(cfg, appContext)
//    private val vad = SileroVadAdapter(appContext, endSilenceMs = 700)
//
//    private var ws: WsClient? = null
//    private var micJob: Job? = null
//
//    val sentBytes = MutableStateFlow(0L)
//    val recvBytes = MutableStateFlow(0L)
//
//    @SuppressLint("MissingPermission")
//    fun start(scope: CoroutineScope, onEndpoint: ()->Unit) {
//        if (micJob != null) {
//            Log.d("VoiceEngine", "start() ignored, already running")
//            return
//        }
//
//        Log.d("VoiceEngine", "Connecting WS: $serverUrl")
//        ws = WsClient(
//            url = serverUrl,
//            onBinary = { bytes ->
//                recvBytes.value += bytes.size
//                Log.d("VoiceEngine", "onBinary recvBytes=${recvBytes.value} (+${bytes.size})")
//            },
//            onOpen = {
//                Log.d("VoiceEngine", "WebSocket OPEN")
//                ws?.sendText("""{"type":"init","codec":"pcm16le","sr":16000}""")
//            },
//            onFail = { t ->
//                Log.e("VoiceEngine", "WebSocket FAIL: ${t.message}", t)
//            }
//        )
//
//        Log.d("VoiceEngine", "Mic start")
//        micJob = scope.launch(Dispatchers.IO) {
//            mic.start().collect { framePcm ->
//                val end = vad.pushAndIsEndpoint(framePcm)
//
//                ws?.sendBinary(framePcm)
//                sentBytes.value += framePcm.size
//                Log.d("VoiceEngine", "sentBytes=${sentBytes.value} (+${framePcm.size})")
//
//                if (end) {
//                    Log.d("VoiceEngine", "VAD endpoint detected → stopping mic")
//                    stop()
//                    withContext(Dispatchers.Main) { onEndpoint() }
//                }
//            }
//        }
//    }
//
//    fun stop() {
//        micJob?.cancel(); micJob = null
//        mic.stop()
//        vad.reset()
//        // ws açık kalabilir (echo için sorun değil)
//    }
//
//    fun release() {
//        stop()
//        ws?.close(); ws = null
//        vad.close()
//    }
//}
