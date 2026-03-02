import { app, BrowserWindow } from 'electron'
import path from 'node:path'
import { setupIpc } from './ipc'
import { startPythonEngine } from '../services/pythonEngine'
import { EngineClient } from '../services/engineClient'
import { LogBuffer } from '../services/logBuffer'

let win: BrowserWindow | null = null

async function createWindow() {
  win = new BrowserWindow({
    width: 1400,
    height: 860,
    backgroundColor: '#0b0b10',
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    await win.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    await win.loadFile(path.join(__dirname, '../renderer/index.html'))
  }

  win.on('closed', () => (win = null))
}

app.whenReady().then(async () => {
  const logs = new LogBuffer(4000)

  // Start python engine (localhost only) + create API client
  const engine = await startPythonEngine({ logs })
  const client = new EngineClient(engine.baseUrl)

  setupIpc({ engine: client, logs })

  await createWindow()

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) await createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
