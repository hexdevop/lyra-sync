export default function Background() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden" aria-hidden>
      {/* Purple orb — top-left */}
      <div
        style={{
          position: 'absolute',
          top: '-10%',
          left: '-15%',
          width: '60vw',
          height: '60vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(124,106,247,0.18) 0%, transparent 70%)',
          filter: 'blur(60px)',
          animation: 'orb1 18s ease-in-out infinite alternate',
        }}
      />
      {/* Blue orb — bottom-right */}
      <div
        style={{
          position: 'absolute',
          bottom: '-15%',
          right: '-10%',
          width: '55vw',
          height: '55vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(91,141,247,0.14) 0%, transparent 70%)',
          filter: 'blur(70px)',
          animation: 'orb2 22s ease-in-out infinite alternate',
        }}
      />
      {/* Magenta orb — center */}
      <div
        style={{
          position: 'absolute',
          top: '35%',
          left: '40%',
          width: '30vw',
          height: '30vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(180,100,247,0.09) 0%, transparent 70%)',
          filter: 'blur(50px)',
          animation: 'orb3 14s ease-in-out infinite alternate',
        }}
      />

      <style>{`
        @keyframes orb1 {
          from { transform: translate(0, 0) scale(1); }
          to   { transform: translate(4vw, 6vh) scale(1.08); }
        }
        @keyframes orb2 {
          from { transform: translate(0, 0) scale(1); }
          to   { transform: translate(-5vw, -4vh) scale(1.1); }
        }
        @keyframes orb3 {
          from { transform: translate(0, 0) scale(1); }
          to   { transform: translate(3vw, -5vh) scale(0.92); }
        }
      `}</style>
    </div>
  )
}
