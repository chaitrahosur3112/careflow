import { useEffect, useRef } from 'react'

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || (
  window.location.protocol === 'https:' ? 'wss://' : 'ws://'
) + window.location.host

/**
 * Subscribes to the Django Channels live-queue feed for a department.
 * onUpdate is called with no payload beyond a signal to refetch — see
 * backend/apps/patients/consumers.py for why the message is kept thin.
 */
export default function useQueueSocket(departmentId, onUpdate) {
  const socketRef = useRef(null)

  useEffect(() => {
    if (!departmentId) return undefined

    const url = `${WS_BASE}/ws/queue-updates/${departmentId}/`
    const socket = new WebSocket(url)
    socketRef.current = socket

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'queue_update') onUpdate?.()
      } catch {
        // ignore malformed frames
      }
    }

    return () => socket.close()
  }, [departmentId, onUpdate])

  return socketRef
}
