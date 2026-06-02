/** Resample mono float32 audio from inputRate to outputRate. */
export function resampleFloat32(input, inputRate, outputRate) {
  if (inputRate === outputRate) return input
  const ratio = inputRate / outputRate
  const outputLength = Math.max(1, Math.round(input.length / ratio))
  const output = new Float32Array(outputLength)
  for (let i = 0; i < outputLength; i++) {
    const srcIndex = i * ratio
    const idx = Math.floor(srcIndex)
    const frac = srcIndex - idx
    const a = input[idx] ?? 0
    const b = input[Math.min(idx + 1, input.length - 1)]
    output[i] = a + frac * (b - a)
  }
  return output
}

export function float32ToPcm16Base64(float32) {
  const buffer = new ArrayBuffer(float32.length * 2)
  const view = new DataView(buffer)
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]))
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

export function pcm16Base64ToFloat32(b64) {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  const int16 = new Int16Array(bytes.buffer)
  const float32 = new Float32Array(int16.length)
  for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768
  return float32
}

export class PcmPlayer {
  constructor(sampleRate) {
    this.sampleRate = sampleRate
    this.ctx = null
    this.nextTime = 0
    this.sources = []
  }

  _ensureContext() {
    if (!this.ctx) {
      this.ctx = new AudioContext()
      this.nextTime = this.ctx.currentTime
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume()
    }
  }

  playBase64(b64) {
    if (!b64) return
    this._ensureContext()
    const float32 = pcm16Base64ToFloat32(b64)
    const buffer = this.ctx.createBuffer(1, float32.length, this.sampleRate)
    buffer.copyToChannel(float32, 0)
    const source = this.ctx.createBufferSource()
    source.buffer = buffer
    source.connect(this.ctx.destination)
    const now = this.ctx.currentTime
    const start = Math.max(now, this.nextTime)
    source.start(start)
    this.nextTime = start + buffer.duration
    this.sources.push(source)
    source.onended = () => {
      this.sources = this.sources.filter((s) => s !== source)
    }
  }

  stop() {
    for (const source of this.sources) {
      try {
        source.stop()
      } catch {
        // already stopped
      }
    }
    this.sources = []
    if (this.ctx) {
      this.nextTime = this.ctx.currentTime
    }
  }

  destroy() {
    this.stop()
    if (this.ctx) {
      this.ctx.close()
      this.ctx = null
    }
  }
}

export class PcmStreamCapture {
  constructor({ sampleRate, onChunk, onActive }) {
    this.targetRate = sampleRate
    this.onChunk = onChunk
    this.onActive = onActive
    this.stream = null
    this.audioContext = null
    this.processor = null
    this.source = null
    this.silentGain = null
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    })
    this.audioContext = new AudioContext()
    this.source = this.audioContext.createMediaStreamSource(this.stream)
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1)
    this.silentGain = this.audioContext.createGain()
    this.silentGain.gain.value = 0

    this.processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0)
      let sum = 0
      for (let i = 0; i < input.length; i++) sum += input[i] * input[i]
      const rms = Math.sqrt(sum / input.length)
      this.onActive?.(rms > 0.01)

      const resampled = resampleFloat32(input, this.audioContext.sampleRate, this.targetRate)
      this.onChunk(float32ToPcm16Base64(resampled))
    }

    this.source.connect(this.processor)
    this.processor.connect(this.silentGain)
    this.silentGain.connect(this.audioContext.destination)
  }

  stop() {
    this.processor?.disconnect()
    this.source?.disconnect()
    this.silentGain?.disconnect()
    this.stream?.getTracks().forEach((t) => t.stop())
    this.audioContext?.close()
    this.processor = null
    this.source = null
    this.silentGain = null
    this.stream = null
    this.audioContext = null
    this.onActive?.(false)
  }
}

export function isVoiceSupported() {
  return (
    typeof window !== 'undefined'
    && !!window.WebSocket
    && !!navigator.mediaDevices?.getUserMedia
    && typeof AudioContext !== 'undefined'
  )
}
