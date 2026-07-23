export default function ShieldLogo({ size = 48 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="shieldGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#60a5fa" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>
      <path d="M24 4L8 10v14c0 9.5 6.8 18.4 16 21 9.2-2.6 16-11.5 16-21V10L24 4z" fill="url(#shieldGrad)" opacity="0.9" />
      <path d="M24 4L8 10v14c0 9.5 6.8 18.4 16 21 9.2-2.6 16-11.5 16-21V10L24 4z" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" fill="none" />
      <path d="M18 24l4 4 8-8" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
