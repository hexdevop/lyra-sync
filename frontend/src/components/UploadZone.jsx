import { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Upload, Music, FileAudio } from 'lucide-react'

export default function UploadZone({ onFile }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)
  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20, scale: 0.97 }}
      transition={{ duration: 0.35 }}
    >
      <div
        className={`drop-zone ${dragging ? 'drag-over' : ''}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".mp3,.wav,.m4a"
          hidden
          onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
        />

        {/* Animated icon */}
        <motion.div
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          className="flex justify-center mb-5"
        >
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: '50%',
              background: 'rgba(124,106,247,0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 32px rgba(124,106,247,0.2)',
            }}
          >
            <Music size={32} color="#7c6af7" strokeWidth={1.5} />
          </div>
        </motion.div>

        <p className="text-faint font-medium text-lg mb-1">
          Перетащи аудиофайл сюда
        </p>
        <p className="text-muted text-sm mb-5">или</p>

        <label className="btn-primary" onClick={(e) => e.stopPropagation()}>
          <Upload size={16} strokeWidth={2} />
          Выбрать файл
        </label>

        <p className="text-muted text-xs mt-5">
          MP3, WAV, M4A · до 50 MB · до 15 минут
        </p>

        {/* Supported formats */}
        <div className="flex justify-center gap-3 mt-4">
          {['MP3', 'WAV', 'M4A'].map(fmt => (
            <span
              key={fmt}
              style={{
                padding: '2px 10px',
                borderRadius: 6,
                border: '1px solid rgba(124,106,247,0.2)',
                fontSize: '0.72rem',
                color: '#5a5a90',
                letterSpacing: '0.05em',
                fontWeight: 600,
              }}
            >
              {fmt}
            </span>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
