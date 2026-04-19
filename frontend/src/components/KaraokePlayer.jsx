import { useState, useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Play, Pause, SkipBack } from 'lucide-react'

function fmtTime(s) {
  if (!s || isNaN(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

export default function KaraokePlayer({ result, objectUrl, onReset }) {
  const [tab, setTab] = useState('karaoke')
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [activeLine, setActiveLine] = useState(-1)
  const [copied, setCopied] = useState(null)

  const audioRef = useRef(null)
  const lineRefs = useRef([])
  const seekBarRef = useRef(null)

  const lines = result?.json || []

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const onTimeUpdate = () => {
      const t = audio.currentTime
      setCurrentTime(t)

      let active = -1
      for (let i = 0; i < lines.length; i++) {
        if (t >= lines[i].start && t < lines[i].end) {
          active = i
          break
        }
      }
      setActiveLine(prev => {
        if (prev !== active && active !== -1 && lineRefs.current[active]) {
          lineRefs.current[active].scrollIntoView({ block: 'center', behavior: 'smooth' })
        }
        return active
      })
    }

    const onLoaded = () => setDuration(audio.duration)
    const onEnded = () => setIsPlaying(false)

    audio.addEventListener('timeupdate', onTimeUpdate)
    audio.addEventListener('loadedmetadata', onLoaded)
    audio.addEventListener('ended', onEnded)
    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate)
      audio.removeEventListener('loadedmetadata', onLoaded)
      audio.removeEventListener('ended', onEnded)
    }
  }, [lines])

  const togglePlay = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return
    if (isPlaying) { audio.pause(); setIsPlaying(false) }
    else { audio.play(); setIsPlaying(true) }
  }, [isPlaying])

  const handleSeek = useCallback((e) => {
    const audio = audioRef.current
    if (!audio || !duration) return
    const rect = e.currentTarget.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    audio.currentTime = ratio * duration
  }, [duration])

  const seekToLine = useCallback((start) => {
    const audio = audioRef.current
    if (!audio) return
    audio.currentTime = start
    audio.play()
    setIsPlaying(true)
  }, [])

  const restartAudio = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return
    audio.currentTime = 0
    audio.play()
    setIsPlaying(true)
  }, [])

  const copy = useCallback((text, key) => {
    navigator.clipboard.writeText(text || '').then(() => {
      setCopied(key)
      setTimeout(() => setCopied(null), 1500)
    })
  }, [])

  const progressPct = duration ? (currentTime / duration) * 100 : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.35 }}
      className="space-y-3"
    >
      <audio ref={audioRef} src={objectUrl} preload="metadata" />

      {/* ── Audio Player Card ─────────────────────────────────────── */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-4">
          {/* Restart */}
          <button
            onClick={restartAudio}
            style={{
              width: 36, height: 36, borderRadius: '50%',
              background: 'rgba(124,106,247,0.1)',
              border: '1px solid rgba(124,106,247,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', flexShrink: 0, transition: 'background 0.15s',
            }}
            title="Сначала"
          >
            <SkipBack size={15} color="#7c6af7" />
          </button>

          {/* Play/Pause */}
          <button className="play-btn" onClick={togglePlay} title={isPlaying ? 'Пауза' : 'Воспроизвести'}>
            {isPlaying
              ? <Pause size={20} color="#fff" fill="#fff" />
              : <Play size={20} color="#fff" fill="#fff" style={{ marginLeft: 2 }} />
            }
          </button>

          {/* Seekbar + time */}
          <div className="flex-1">
            <div
              ref={seekBarRef}
              className="seek-bar mb-1.5"
              style={{ '--progress': `${progressPct}%` }}
              onClick={handleSeek}
            >
              <div className="seek-bar-fill" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="flex justify-between" style={{ fontSize: '0.72rem', color: '#5a5a90' }}>
              <span>{fmtTime(currentTime)}</span>
              <span>{fmtTime(duration)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Content Card ──────────────────────────────────────────── */}
      <div className="glass-card">
        {/* Tabs */}
        <div className="flex border-b" style={{ borderColor: 'rgba(124,106,247,0.1)' }}>
          {[
            { id: 'karaoke', label: 'KARAOKE' },
            { id: 'lrc',     label: 'LRC' },
            { id: 'srt',     label: 'SRT' },
          ].map(t => (
            <button
              key={t.id}
              className={`tab-btn ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="p-4">
          {/* Karaoke tab */}
          {tab === 'karaoke' && (
            <div className="lyrics-scroll">
              {lines.length === 0 ? (
                <p className="text-muted text-center py-8 text-sm">
                  Текст не найден
                </p>
              ) : (
                lines.map((ln, i) => {
                  const isActive = i === activeLine
                  const dist = activeLine === -1 ? 0 : Math.abs(i - activeLine)
                  return (
                    <div
                      key={i}
                      ref={el => { lineRefs.current[i] = el }}
                      className={`lyric-line ${isActive ? 'active' : ''}`}
                      style={{
                        opacity: activeLine === -1 ? 0.65 : isActive ? 1 : Math.max(0.18, 0.65 - dist * 0.12),
                        transform: `scale(${isActive ? 1 : Math.max(0.93, 1 - dist * 0.018)})`,
                      }}
                      onClick={() => seekToLine(ln.start)}
                    >
                      {ln.text}
                    </div>
                  )
                })
              )}
            </div>
          )}

          {/* LRC tab */}
          {tab === 'lrc' && (
            <div>
              <pre className="raw-text">{result?.lrc || '(пусто)'}</pre>
              <button className="copy-btn" onClick={() => copy(result?.lrc, 'lrc')}>
                {copied === 'lrc' ? '✓ Скопировано' : 'Копировать LRC'}
              </button>
            </div>
          )}

          {/* SRT tab */}
          {tab === 'srt' && (
            <div>
              <pre className="raw-text">{result?.srt || '(пусто)'}</pre>
              <button className="copy-btn" onClick={() => copy(result?.srt, 'srt')}>
                {copied === 'srt' ? '✓ Скопировано' : 'Копировать SRT'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Reset */}
      <button className="btn-ghost" onClick={onReset}>
        ← Загрузить другой файл
      </button>
    </motion.div>
  )
}
