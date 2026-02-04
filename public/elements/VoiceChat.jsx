/**
 * VoiceChat - Real-Time Voice Conversation with Lawrence
 * =======================================================
 *
 * Captures microphone audio, sends to Mindrian voice server,
 * receives and plays AI responses with YOUR CUSTOM ElevenLabs voice.
 *
 * ONLY FOR LAWRENCE CHAT - PWS thinking partner voice mode.
 *
 * Props:
 * - serverUrl: WebSocket URL (default: ws://localhost:8765)
 * - showTranscript: Show conversation transcript (default: true)
 */

export default function VoiceChat() {
  // Chainlit APIs
  const { callAction, sendUserMessage } = window.Chainlit || {}

  // Props with defaults - Lawrence only, no agent switching
  const {
    serverUrl = "ws://localhost:8765",
    showTranscript = true,
  } = props || {}

  // State - Lawrence only
  const [isConnected, setIsConnected] = React.useState(false)
  const [isListening, setIsListening] = React.useState(false)
  const [isSpeaking, setIsSpeaking] = React.useState(false)
  const [transcript, setTranscript] = React.useState([])
  const [currentText, setCurrentText] = React.useState("")
  const [error, setError] = React.useState(null)
  const [audioLevel, setAudioLevel] = React.useState(0)

  // Lawrence is the only agent
  const agentName = "Lawrence"

  // Refs
  const wsRef = React.useRef(null)
  const audioContextRef = React.useRef(null)
  const mediaStreamRef = React.useRef(null)
  const processorRef = React.useRef(null)
  const audioQueueRef = React.useRef([])
  const isPlayingRef = React.useRef(false)

  // ─────────────────────────────────────────────────────────────────
  // WebSocket Connection
  // ─────────────────────────────────────────────────────────────────

  const connect = React.useCallback(async () => {
    try {
      setError(null)
      const ws = new WebSocket(serverUrl)

      ws.onopen = () => {
        console.log("🎤 Voice connected")
        setIsConnected(true)
      }

      ws.onclose = () => {
        console.log("🔌 Voice disconnected")
        setIsConnected(false)
        setIsListening(false)
      }

      ws.onerror = (e) => {
        console.error("Voice error:", e)
        setError("Connection failed. Is the voice server running?")
      }

      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        await handleServerMessage(data)
      }

      wsRef.current = ws

    } catch (err) {
      setError(`Failed to connect: ${err.message}`)
    }
  }, [serverUrl])

  const disconnect = React.useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    stopListening()
    setIsConnected(false)
  }, [])

  // ─────────────────────────────────────────────────────────────────
  // Handle Server Messages
  // ─────────────────────────────────────────────────────────────────

  const handleServerMessage = async (data) => {
    switch (data.type) {
      case "session_started":
        // Lawrence session started
        console.log("🎤 Voice session with Lawrence started")
        break

      case "transcript":
        // User's speech was transcribed
        setTranscript(prev => [...prev, { role: "user", text: data.text }])
        // Also send to Chainlit chat for persistence
        if (sendUserMessage) {
          sendUserMessage({ content: `🎤 ${data.text}` })
        }
        break

      case "response_start":
        setCurrentText("")
        setIsSpeaking(true)
        break

      case "response_chunk":
        setCurrentText(prev => prev + data.text)
        break

      case "response_end":
        setTranscript(prev => [...prev, { role: "assistant", text: data.text }])
        setCurrentText("")
        break

      case "audio":
      case "audio_chunk":
        // Queue audio for playback (your custom ElevenLabs voice!)
        const audioData = base64ToArrayBuffer(data.audio)
        audioQueueRef.current.push(audioData)
        playNextAudio()
        break

      case "session_ended":
        disconnect()
        break
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // Audio Recording (Microphone)
  // ─────────────────────────────────────────────────────────────────

  const startListening = async () => {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      })

      mediaStreamRef.current = stream

      // Create audio context for processing
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      })
      audioContextRef.current = audioContext

      const source = audioContext.createMediaStreamSource(stream)

      // Create processor for audio chunks
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      processorRef.current = processor

      // Buffer for accumulating audio
      let audioBuffer = []
      let silenceStart = null
      const SILENCE_THRESHOLD = 0.01
      const SILENCE_DURATION = 1500 // ms

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0)

        // Calculate audio level for visualization
        let sum = 0
        for (let i = 0; i < inputData.length; i++) {
          sum += Math.abs(inputData[i])
        }
        const level = sum / inputData.length
        setAudioLevel(Math.min(1, level * 10))

        // Check for silence
        const isSilent = level < SILENCE_THRESHOLD

        if (isSilent) {
          if (!silenceStart) {
            silenceStart = Date.now()
          } else if (Date.now() - silenceStart > SILENCE_DURATION && audioBuffer.length > 0) {
            // End of utterance - send audio
            sendAudioToServer(audioBuffer)
            audioBuffer = []
            silenceStart = null
          }
        } else {
          silenceStart = null
          // Convert to 16-bit PCM
          const pcmData = floatTo16BitPCM(inputData)
          audioBuffer.push(...pcmData)
        }
      }

      source.connect(processor)
      processor.connect(audioContext.destination)

      setIsListening(true)
      console.log("🎤 Listening started")

    } catch (err) {
      setError(`Microphone error: ${err.message}`)
    }
  }

  const stopListening = () => {
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
      mediaStreamRef.current = null
    }
    setIsListening(false)
    setAudioLevel(0)
    console.log("🎤 Listening stopped")
  }

  const sendAudioToServer = (audioBuffer) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    // Convert to Uint8Array and base64
    const uint8Array = new Uint8Array(audioBuffer)
    const base64Audio = arrayBufferToBase64(uint8Array.buffer)

    wsRef.current.send(JSON.stringify({
      type: "audio",
      audio: base64Audio,
      sample_rate: 16000,
    }))
  }

  // ─────────────────────────────────────────────────────────────────
  // Audio Playback (TTS Response)
  // ─────────────────────────────────────────────────────────────────

  const playNextAudio = async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return

    isPlayingRef.current = true

    while (audioQueueRef.current.length > 0) {
      const audioData = audioQueueRef.current.shift()
      await playAudioChunk(audioData)
    }

    isPlayingRef.current = false
    setIsSpeaking(false)
  }

  const playAudioChunk = async (arrayBuffer) => {
    return new Promise((resolve) => {
      const audio = new Audio()
      const blob = new Blob([arrayBuffer], { type: "audio/mpeg" })
      audio.src = URL.createObjectURL(blob)

      audio.onended = () => {
        URL.revokeObjectURL(audio.src)
        resolve()
      }

      audio.onerror = () => {
        resolve()
      }

      audio.play().catch(() => resolve())
    })
  }

  // Interrupt playback if user starts speaking
  const handleInterrupt = () => {
    audioQueueRef.current = []
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "interrupt" }))
    }
  }


  // ─────────────────────────────────────────────────────────────────
  // Utility Functions
  // ─────────────────────────────────────────────────────────────────

  const floatTo16BitPCM = (float32Array) => {
    const result = []
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]))
      const val = s < 0 ? s * 0x8000 : s * 0x7FFF
      result.push(val & 0xFF)
      result.push((val >> 8) & 0xFF)
    }
    return result
  }

  const arrayBufferToBase64 = (buffer) => {
    const bytes = new Uint8Array(buffer)
    let binary = ""
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  const base64ToArrayBuffer = (base64) => {
    const binary = atob(base64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    return bytes.buffer
  }

  // ─────────────────────────────────────────────────────────────────
  // Effects
  // ─────────────────────────────────────────────────────────────────

  React.useEffect(() => {
    if (autoStart) {
      connect()
    }
    return () => {
      disconnect()
    }
  }, [])

  // ─────────────────────────────────────────────────────────────────
  // Render - Lawrence Voice Chat Only
  // ─────────────────────────────────────────────────────────────────

  return (
    <Card className="voice-chat-container">
      {/* Header */}
      <CardHeader>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "24px" }}>🎙️</span>
            <CardTitle>Talk to Lawrence</CardTitle>
          </div>
          <Badge variant={isConnected ? "default" : "secondary"}>
            {isConnected ? "🟢 Live" : "⚪ Offline"}
          </Badge>
        </div>
        <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px" }}>
          Real-time voice conversation with your PWS thinking partner
        </div>
      </CardHeader>

      <CardContent>
        {/* Error Display */}
        {error && (
          <div style={{
            padding: "12px",
            marginBottom: "16px",
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            borderRadius: "8px",
            color: "#ef4444",
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Voice Control */}
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "24px",
          marginBottom: "16px",
        }}>
          {/* Audio Level Indicator */}
          <div style={{
            width: "120px",
            height: "120px",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: "16px",
            backgroundColor: isListening
              ? `rgba(34, 197, 94, ${0.2 + audioLevel * 0.5})`
              : isSpeaking
                ? "rgba(59, 130, 246, 0.3)"
                : "rgba(148, 163, 184, 0.2)",
            border: `3px solid ${isListening ? "#22c55e" : isSpeaking ? "#3b82f6" : "#94a3b8"}`,
            transition: "all 0.1s ease",
            transform: `scale(${1 + audioLevel * 0.1})`,
          }}>
            <span style={{ fontSize: "48px" }}>
              {isListening ? "🎤" : isSpeaking ? "🔊" : "🎙️"}
            </span>
          </div>

          {/* Status Text */}
          <div style={{
            fontSize: "14px",
            color: "#64748b",
            marginBottom: "16px",
            textAlign: "center",
          }}>
            {isListening ? "Listening... (speak now)" :
             isSpeaking ? `${agentName} is speaking...` :
             isConnected ? "Click to start" : "Connect to begin"}
          </div>

          {/* Control Buttons */}
          <div style={{ display: "flex", gap: "12px" }}>
            {!isConnected ? (
              <Button onClick={connect} size="lg">
                🔌 Connect
              </Button>
            ) : (
              <>
                {!isListening ? (
                  <Button onClick={startListening} size="lg" variant="default">
                    🎤 Start Listening
                  </Button>
                ) : (
                  <Button onClick={stopListening} size="lg" variant="destructive">
                    ⏹️ Stop
                  </Button>
                )}
                <Button onClick={disconnect} variant="outline">
                  Disconnect
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Current Response (streaming) */}
        {currentText && (
          <div style={{
            padding: "12px",
            marginBottom: "16px",
            backgroundColor: "rgba(59, 130, 246, 0.1)",
            borderRadius: "8px",
            borderLeft: "4px solid #3b82f6",
          }}>
            <strong>{agentName}:</strong> {currentText}
            <span className="typing-indicator">▋</span>
          </div>
        )}

        {/* Transcript */}
        {showTranscript && transcript.length > 0 && (
          <div style={{
            maxHeight: "200px",
            overflowY: "auto",
            padding: "12px",
            backgroundColor: "rgba(0, 0, 0, 0.02)",
            borderRadius: "8px",
          }}>
            <div style={{ fontSize: "12px", fontWeight: "600", marginBottom: "8px", color: "#64748b" }}>
              Conversation
            </div>
            {transcript.slice(-6).map((msg, i) => (
              <div
                key={i}
                style={{
                  padding: "8px",
                  marginBottom: "8px",
                  borderRadius: "6px",
                  backgroundColor: msg.role === "user"
                    ? "rgba(34, 197, 94, 0.1)"
                    : "rgba(59, 130, 246, 0.1)",
                }}
              >
                <strong>{msg.role === "user" ? "You" : agentName}:</strong> {msg.text}
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {/* Footer */}
      <CardFooter>
        <div style={{ fontSize: "12px", color: "#94a3b8", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>🎤 Google STT</span>
          <span>→</span>
          <span>🧠 Gemini</span>
          <span>→</span>
          <span>🔊 Your Custom Voice</span>
        </div>
      </CardFooter>

      <style>{`
        .typing-indicator {
          animation: blink 1s infinite;
        }
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </Card>
  )
}
