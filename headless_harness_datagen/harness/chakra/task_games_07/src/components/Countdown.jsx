import { useState, useEffect } from 'react'

export default function Countdown({ onDone }) {
  const [count, setCount] = useState(3)

  useEffect(() => {
    if (count <= 0) {
      onDone()
      return
    }
    const timer = setTimeout(() => setCount((c) => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [count, onDone])

  return (
    <div className="countdown fade-in">
      {count > 0 ? count : 'GO!'}
    </div>
  )
}
