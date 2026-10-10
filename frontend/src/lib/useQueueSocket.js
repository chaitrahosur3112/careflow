import { useEffect, useRef } from 'react'

const configuredWsBase = import.meta.env.VITE_WS_BASE_URL
const rawWsBase = configuredWsBase
  ? configuredWsBase.replace(/^https:/i, 'wss:').replace(/^http:/i, 'ws:')
  : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
const WS_BASE = rawWsBase.replace(/\/+$/, '')

/**
 * Subscribes to the Django Channels live-queue feed for a department.
 * onUpdate is called with no payload beyond a signal to refetch — see
 * backend/apps/patients/consumers.py for why the message is kept thin.
 */
export default function useQueueSocket(departmentId, onUpdate) {
  const socketRef = useRef(null)

  useEffect(() => {
    if (!departmentId) return undefined

    let isSubscribed = true
    let retryTimer = null

    function connect() {
      if (!isSubscribed) return
      try {
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

        socket.onclose = () => {
          if (isSubscribed) {
            retryTimer = setTimeout(connect, 3000)
          }
        }

        socket.onerror = () => {
          try {
            socket.close()
          } catch {
            // ignore
          }
        }
      } catch {
        if (isSubscribed) {
          retryTimer = setTimeout(connect, 5000)
        }
      }
    }

    connect()

    return () => {
      isSubscribed = false
      if (retryTimer) clearTimeout(retryTimer)
      if (socketRef.current) {
        socketRef.current.close()
      }
    }
  }, [departmentId, onUpdate])

  return socketRef
}
