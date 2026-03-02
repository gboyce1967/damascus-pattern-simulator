export class EngineClient {
  constructor(private baseUrl: string) {}

  private async j<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) }
    })
    if (!res.ok) throw new Error(`Engine error ${res.status}: ${await res.text()}`)
    return res.json() as Promise<T>
  }

  health() {
    return this.j('/health')
  }

  createSession(args: any) {
    return this.j('/sessions', { method: 'POST', body: JSON.stringify(args) })
  }

  getMesh(sessionId: string) {
    return this.j(`/sessions/${sessionId}/mesh`)
  }

  getStats(sessionId: string) {
    return this.j(`/sessions/${sessionId}/stats`)
  }

  applyOperation(sessionId: string, op: string, payload: any) {
    return this.j(`/sessions/${sessionId}/op/${op}`, { method: 'POST', body: JSON.stringify(payload || {}) })
  }

  getCrossSection(sessionId: string, payload: any) {
    return this.j(`/sessions/${sessionId}/cross_section`, { method: 'POST', body: JSON.stringify(payload || {}) })
  }

  exportModel(sessionId: string, payload: any) {
    return this.j(`/sessions/${sessionId}/export/model`, { method: 'POST', body: JSON.stringify(payload || {}) })
  }

  referenceList() {
    return this.j('/reference/list')
  }

  referenceGet(id: string) {
    return this.j(`/reference/get/${encodeURIComponent(id)}`)
  }
}
