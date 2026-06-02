import { ref, reactive } from 'vue'
import { api } from '@/api/index.js'
import { eventsToTranscriptEntries, lastTranscriptEntry } from '@/utils/interviewHelpers.js'
import { PcmPlayer, PcmStreamCapture } from '@/utils/voiceAudio.js'

export function useVoiceInterview({ sessionId, profileId, userId = 'default' }) {
  const connected = ref(false)
  const connecting = ref(false)
  const error = ref(null)
  const hintText = ref('等待开始')
  const avatarSpeaking = ref(false)
  const isListening = ref(false)
  const transcriptEntries = ref([])
  const liveAiText = ref('')
  const waveformActive = ref(false)

  let ws = null
  let capture = null
  let player = null
  let isMuted = false
  let isPaused = false
  let inputSampleRate = 24000
  let outputSampleRate = 24000

  function formatVoiceError(payload) {
    const code = payload?.code || ''
    const message = payload?.message || ''
    if (
      code === 'realtime_not_configured'
      || message.includes('DASHSCOPE_API_KEY')
      || message.includes('OPENAI_API_KEY')
      || message.includes('未配置')
    ) {
      return '语音面试 API Key 未配置，请在 backend/.env 中设置 DASHSCOPE_API_KEY 后重启后端'
    }
    if (message.includes('websocket connection') || message.includes('无法连接 DashScope')) {
      return '无法连接 DashScope 实时语音服务，请检查网络、API Key 与防火墙设置'
    }
    return message || '连接出错'
  }

  function send(msg) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg))
    }
  }

  function appendTranscript(label, text) {
    const trimmed = (text || '').trim()
    if (!trimmed) return
    transcriptEntries.value.push({ label, text: trimmed })
  }

  async function loadHistory() {
    const data = await api.getSessionEvents(sessionId)
    const last = lastTranscriptEntry(data.events || [])
    transcriptEntries.value = last ? [last] : []
  }

  async function startCapture() {
    if (isMuted || isPaused || capture) return
    try {
      if (!player) {
        player = new PcmPlayer(outputSampleRate)
      }
      capture = new PcmStreamCapture({
        sampleRate: inputSampleRate,
        onChunk: (b64) => {
          if (!isMuted && !isPaused && ws?.readyState === WebSocket.OPEN) {
            send({ type: 'user.audio.chunk', payload: { audio: b64 } })
          }
        },
        onActive: (active) => {
          waveformActive.value = active && !isMuted && !isPaused && avatarSpeaking.value === false
        },
      })
      await capture.start()
      isListening.value = !isMuted && !isPaused
    } catch (e) {
      error.value = '无法访问麦克风，请检查权限'
      hintText.value = error.value
      throw e
    }
  }

  function stopCapture() {
    capture?.stop()
    capture = null
    isListening.value = false
    waveformActive.value = false
  }

  function handleServerEvent(data) {
    switch (data.type) {
      case 'session.started': {
        const audio = data.payload?.audio || {}
        inputSampleRate = audio.input_sample_rate ?? 24000
        outputSampleRate = audio.output_sample_rate ?? 24000
        startCapture().catch(() => {})
        hintText.value = '请开始说话...'
        break
      }
      case 'user.transcript':
        appendTranscript('你', data.payload?.text || '')
        break
      case 'assistant.transcript.delta':
        liveAiText.value += data.payload?.text ?? ''
        avatarSpeaking.value = true
        waveformActive.value = false
        break
      case 'assistant.transcript.done': {
        const text = data.payload?.text || liveAiText.value
        liveAiText.value = ''
        appendTranscript('Capy', text)
        avatarSpeaking.value = false
        break
      }
      case 'assistant.audio.delta':
        avatarSpeaking.value = true
        waveformActive.value = false
        player?.playBase64(data.payload?.audio)
        break
      case 'assistant.audio.done':
        break
      case 'ai.interrupted':
        player?.stop()
        avatarSpeaking.value = false
        liveAiText.value = ''
        break
      case 'error':
        error.value = formatVoiceError(data.payload)
        hintText.value = error.value
        break
      case 'cost.limit_reached':
        error.value = '语音面试时长已达上限'
        hintText.value = error.value
        disconnect()
        break
      case 'turn.done':
        disconnect()
        break
      default:
        break
    }
  }

  async function connect() {
    if (connecting.value || connected.value) return
    connecting.value = true
    error.value = null
    hintText.value = '正在连接...'

    try {
      await loadHistory()

      ws = new WebSocket(api.getVoiceWebSocketUrl(sessionId, { profileId, userId }))

      await new Promise((resolve, reject) => {
        ws.onopen = () => resolve()
        ws.onerror = () => reject(new Error('WebSocket 连接失败'))
        ws.onclose = (evt) => {
          if (!connected.value) {
            reject(new Error(`WebSocket 已关闭 (${evt.code})`))
          }
        }
      })

      ws.onmessage = (event) => {
        try {
          handleServerEvent(JSON.parse(event.data))
        } catch (e) {
          console.error('Invalid WS message:', e)
        }
      }

      ws.onclose = () => {
        connected.value = false
        stopCapture()
        player?.destroy()
        player = null
      }

      connected.value = true
      connecting.value = false
    } catch (e) {
      connecting.value = false
      connected.value = false
      error.value = e.message || '连接失败'
      hintText.value = error.value
      ws?.close()
      ws = null
    }
  }

  function disconnect() {
    stopCapture()
    player?.destroy()
    player = null
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    connected.value = false
    avatarSpeaking.value = false
    isListening.value = false
    waveformActive.value = false
  }

  function setMuted(muted) {
    isMuted = muted
    if (muted) {
      isListening.value = false
      waveformActive.value = false
      hintText.value = '已静音'
    } else if (connected.value && !isPaused) {
      hintText.value = '请开始说话...'
      isListening.value = !!capture
    }
  }

  function setPaused(paused) {
    isPaused = paused
    if (paused) {
      isListening.value = false
      waveformActive.value = false
      hintText.value = '面试已暂停'
    } else if (connected.value && !isMuted) {
      hintText.value = '请开始说话...'
      isListening.value = !!capture
      if (!capture) {
        startCapture().catch(() => {})
      }
    }
  }

  function clearTranscript() {
    transcriptEntries.value = []
    liveAiText.value = ''
  }

  return reactive({
    connected,
    connecting,
    error,
    hintText,
    avatarSpeaking,
    isListening,
    transcriptEntries,
    liveAiText,
    waveformActive,
    connect,
    disconnect,
    setMuted,
    setPaused,
    loadHistory,
    clearTranscript,
  })
}
