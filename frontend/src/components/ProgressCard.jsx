import { motion } from 'framer-motion'

const STEPS = [
  'Загрузка файла',
  'Предобработка аудио',
  'Разделение вокала',
  'Распознавание текста',
  'Поиск текста песни',
  'Синхронизация',
]

const WAVE_DELAYS = [0, 0.1, 0.2, 0.3, 0.15, 0.25, 0.05, 0.35, 0.12, 0.22, 0.08, 0.18]
const WAVE_HEIGHTS = [16, 28, 40, 32, 24, 36, 20, 40, 28, 34, 18, 30]

export default function ProgressCard({ stepIdx, progress }) {
  return (
    <motion.div
      className="glass-card p-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.35 }}
    >
      {/* Waveform animation */}
      <div className="flex justify-center mb-7">
        <div className="wave-bars">
          {WAVE_HEIGHTS.map((h, i) => (
            <div
              key={i}
              className="wave-bar"
              style={{
                height: h,
                animationDelay: `${WAVE_DELAYS[i]}s`,
                animationDuration: `${0.9 + (i % 3) * 0.15}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Current step label */}
      <p className="text-center text-faint font-medium mb-1">
        {STEPS[stepIdx]}…
      </p>
      <p className="text-center text-muted text-sm mb-6">
        Это может занять несколько минут
      </p>

      {/* Progress bar */}
      <div className="progress-track mb-6">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {/* Step indicators */}
      <div className="flex items-start gap-2">
        {STEPS.map((label, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1.5">
            <div
              className={`step-dot ${i < stepIdx ? 'done' : i === stepIdx ? 'active' : ''}`}
            />
            <span
              className="text-center leading-tight"
              style={{
                fontSize: '0.65rem',
                color: i <= stepIdx ? 'rgba(124,106,247,0.9)' : '#3a3a60',
                transition: 'color 0.3s',
              }}
            >
              {label}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
