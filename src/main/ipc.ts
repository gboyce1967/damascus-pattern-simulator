import { ipcMain, dialog, app } from 'electron'
import { EngineClient } from '../services/engineClient'
import { LogBuffer } from '../services/logBuffer'
import { ProjectStore } from '../services/projectStore'

export function setupIpc(opts: { engine: EngineClient; logs: LogBuffer }) {
  const { engine, logs } = opts
  const store = new ProjectStore(app.getPath('userData'))

  ipcMain.handle('app:getInfo', async () => {
    return {
      name: 'Damascus Builder 3D',
      userDataPath: app.getPath('userData')
    }
  })

  ipcMain.handle('engine:health', async () => engine.health())

  ipcMain.handle('engine:createSession', async (_evt, args) => engine.createSession(args))
  ipcMain.handle('engine:mesh', async (_evt, sessionId: string) => engine.getMesh(sessionId))
  ipcMain.handle('engine:stats', async (_evt, sessionId: string) => engine.getStats(sessionId))

  ipcMain.handle('engine:op', async (_evt, sessionId: string, op: string, payload: any) => {
    return engine.applyOperation(sessionId, op, payload)
  })

  ipcMain.handle('engine:crossSection', async (_evt, sessionId: string, payload: any) => {
    return engine.getCrossSection(sessionId, payload)
  })

  ipcMain.handle('engine:referenceList', async () => engine.referenceList())
  ipcMain.handle('engine:referenceGet', async (_evt, id: string) => engine.referenceGet(id))

  ipcMain.handle('export:model', async (_evt, sessionId: string, mergeLayers: boolean) => {
    const { canceled, filePath } = await dialog.showSaveDialog({
      title: 'Export 3D Model',
      defaultPath: 'billet.obj',
      filters: [
        { name: 'Wavefront OBJ', extensions: ['obj'] },
        { name: 'STL', extensions: ['stl'] },
        { name: 'PLY', extensions: ['ply'] }
      ]
    })
    if (canceled || !filePath) return { ok: false }

    return engine.exportModel(sessionId, { path: filePath, merge_layers: mergeLayers })
  })

  ipcMain.handle('projects:list', async () => store.list())
  ipcMain.handle('projects:save', async (_evt, proj: any) => store.save(proj))
  ipcMain.handle('projects:delete', async (_evt, id: string) => store.remove(id))

  ipcMain.handle('logs:tail', async (_evt, n: number) => logs.tail(n))
}
