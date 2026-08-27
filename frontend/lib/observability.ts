type LogLevel = 'info' | 'warn' | 'error'

type Context = Record<string, string | number | boolean | null | undefined>

function clean(context: Context) {
  return Object.fromEntries(Object.entries(context).filter(([, value]) => value !== undefined))
}

export function requestId(request: Request) {
  return request.headers.get('x-vercel-id')
    ?? request.headers.get('x-request-id')
    ?? crypto.randomUUID()
}

export function logEvent(level: LogLevel, event: string, context: Context = {}) {
  const payload = JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    event,
    ...clean(context),
  })

  if (level === 'error') console.error(payload)
  else if (level === 'warn') console.warn(payload)
  else console.info(payload)
}
