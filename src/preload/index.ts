import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('damascus', {
  appInfo: () => ipcRenderer.invoke('app:getInfo'),
  health: () => ipcRenderer.invoke('engine:health'),

  createSession: (args: any) => ipcRenderer.invoke('engine:createSession', args),
  mesh: (sessionId: string) => ipcRenderer.invoke('engine:mesh', sessionId),
  stats: (sessionId: string) => ipcRenderer.invoke('engine:stats', sessionId),

  op: (sessionId: string, op: string, payload?: any) =>
    ipcRenderer.invoke('engine:op', sessionId, op, payload),

  crossSection: (sessionId: string, payload?: any) =>
    ipcRenderer.invoke('engine:crossSection', sessionId, payload),

  exportModel: (sessionId: string, mergeLayers: boolean) =>
    ipcRenderer.invoke('export:model', sessionId, mergeLayers),

  referenceList: () => ipcRenderer.invoke('engine:referenceList'),
  referenceGet: (id: string) => ipcRenderer.invoke('engine:referenceGet', id),

  projectsList: () => ipcRenderer.invoke('projects:list'),
  projectsSave: (p: any) => ipcRenderer.invoke('projects:save', p),
  projectsDelete: (id: string) => ipcRenderer.invoke('projects:delete', id),

  logsTail: (n: number) => ipcRenderer.invoke('logs:tail', n),

  // Preferences
  prefsGet: () => ipcRenderer.invoke('prefs:get'),
  prefsSet: (partial: any) => ipcRenderer.invoke('prefs:set', partial),

  // Menu events (main → renderer)
  onMenuOpenPreferences: (cb: () => void) => {
    const handler = () => cb()
    ipcRenderer.on('menu:open-preferences', handler)
    return () => { ipcRenderer.removeListener('menu:open-preferences', handler) }
  }
})
