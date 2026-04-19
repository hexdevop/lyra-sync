import { useState, useCallback, useRef } from 'react'

const API = '/api'

export default function useAudio() {
  const [state, setState] = useState('upload')
  const [stepIdx, setStepIdx] = useState(0)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [objectUrl, setObjectUrl] = useState(null)
  const [error, setError] = useState(null)

  const pollRef = useRef(null)
  const objectUrlRef = useRef(null)

  const showError = useCallback((msg) => {
    setError(msg)
    setTimeout(() => setError(null), 4000)
    setState('upload')
  }, [])

  const loadResult = useCallback(async (id) => {
    try {
      const res = await fetch(`${API}/audio/${id}/result`)
      if (!res.ok) { showError('Не удалось получить результат'); return }
      const data = await res.json()
      setResult(data)
      setState('done')
    } catch {
      showError('Не удалось загрузить результат')
    }
  }, [showError])

  const startPolling = useCallback((id) => {
    let step = 0
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/audio/${id}/status`)
        const data = await res.json()

        if (data.status === 'processing') {
          step = Math.min(step + 1, 5)
          setStepIdx(step)
          setProgress(20 + step * 13)
        } else if (data.status === 'done') {
          clearInterval(pollRef.current)
          setProgress(100)
          setTimeout(() => loadResult(id), 500)
        } else if (data.status === 'failed') {
          clearInterval(pollRef.current)
          showError(data.error_message || 'Обработка завершилась с ошибкой')
        }
      } catch { /* ignore transient errors */ }
    }, 3000)
  }, [loadResult, showError])

  const handleFile = useCallback(async (file) => {
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['mp3', 'wav', 'm4a'].includes(ext)) {
      showError('Поддерживаются только MP3, WAV, M4A')
      return
    }
    if (file.size > 50 * 1024 * 1024) {
      showError('Файл превышает 50 MB')
      return
    }

    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current)
    const url = URL.createObjectURL(file)
    objectUrlRef.current = url
    setObjectUrl(url)

    clearInterval(pollRef.current)
    setState('processing')
    setStepIdx(0)
    setProgress(5)
    setResult(null)

    const form = new FormData()
    form.append('file', file)

    let res
    try {
      res = await fetch(`${API}/audio/upload`, { method: 'POST', body: form })
    } catch {
      showError('Ошибка соединения с сервером')
      return
    }

    if (!res.ok) {
      const e = await res.json().catch(() => ({}))
      showError(e.detail || `Ошибка ${res.status}`)
      return
    }

    const data = await res.json()

    if (data.status === 'done') {
      setProgress(100)
      await loadResult(data.audio_id)
      return
    }

    setProgress(15)
    startPolling(data.audio_id)
  }, [showError, loadResult, startPolling])

  const reset = useCallback(() => {
    clearInterval(pollRef.current)
    setResult(null)
    setStepIdx(0)
    setProgress(0)
    setError(null)
    setState('upload')
  }, [])

  return { state, progress, stepIdx, result, objectUrl, error, handleFile, reset }
}
