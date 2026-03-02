export {}

declare global {
  interface Window {
    damascus: {
      appInfo(): Promise<{ name: string; userDataPath: string }>
      health(): Promise<any>

      createSession(args: any): Promise<any>
      mesh(sessionId: string): Promise<any>
      stats(sessionId: string): Promise<any>

      op(sessionId: string, op: string, payload?: any): Promise<any>
      crossSection(sessionId: string, payload?: any): Promise<any>

      exportModel(sessionId: string, mergeLayers: boolean): Promise<any>

      referenceList(): Promise<any>
      referenceGet(id: string): Promise<any>

      projectsList(): Promise<any>
      projectsSave(p: any): Promise<any>
      projectsDelete(id: string): Promise<any>

      logsTail(n: number): Promise<string[]>
    }
  }
}
