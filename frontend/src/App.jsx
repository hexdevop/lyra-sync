import { AnimatePresence, motion } from 'framer-motion'
import Background from './components/Background'
import UploadZone from './components/UploadZone'
import ProgressCard from './components/ProgressCard'
import KaraokePlayer from './components/KaraokePlayer'
import useAudio from './hooks/useAudio'

export default function App() {
  const { state, progress, stepIdx, result, objectUrl, error, handleFile, reset } = useAudio()

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-start px-4 py-14 overflow-x-hidden">
      <Background />

      <div className="relative z-10 w-full max-w-[680px]">
        {/* Header */}
        <motion.header
          className="text-center mb-10"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-3 mb-2">
            <span className="text-3xl select-none">🎵</span>
            <h1
              className="text-[2.6rem] font-bold tracking-tight"
              style={{
                background: 'linear-gradient(135deg, #a599ff 0%, #7c6af7 60%, #5b8df7 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              LyraSync
            </h1>
          </div>
          <p className="text-muted text-sm tracking-wide">
            Загрузи песню — получи текст с таймкодами
          </p>
        </motion.header>

        {/* Screens */}
        <AnimatePresence mode="wait">
          {state === 'upload' && (
            <UploadZone key="upload" onFile={handleFile} />
          )}
          {state === 'processing' && (
            <ProgressCard key="processing" stepIdx={stepIdx} progress={progress} />
          )}
          {state === 'done' && result && (
            <KaraokePlayer key="karaoke" result={result} objectUrl={objectUrl} onReset={reset} />
          )}
        </AnimatePresence>
      </div>

      {/* Error toast */}
      <AnimatePresence>
        {error && (
          <motion.div
            className="error-toast"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
