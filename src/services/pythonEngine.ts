import { spawn } from 'node:child_process'
import path from 'node:path'
import fs from 'node:fs'
import net from 'node:net'
import { LogBuffer } from './logBuffer'

async function findFreePort(): Promise<number> {
  return await new Promise((resolve, reject) => {
    const srv = net.createServer()
    srv.listen(0, '127.0.0.1', () => {
      const addr = srv.address()
      srv.close(() => {
        if (typeof addr === 'object' && addr?.port) resolve(addr.port)
        else reject(new Error('Failed to acquire free port'))
      })
    })
  })
}

function resolvePythonExe(projectRoot: string) {
  const isWin = process.platform === 'win32'
  const venvPy = isWin
    ? path.join(projectRoot, '.venv', 'Scripts', 'python.exe')
    : path.join(projectRoot, '.venv', 'bin', 'python')

  if (fs.existsSync(venvPy)) return venvPy
  return isWin ? 'python' : 'python3'
}

async function waitForHealth(url: string, timeoutMs = 12000) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url)
      if (res.ok) return
    } catch {}
    await new Promise(r => setTimeout(r, 250))
  }
  throw new Error('Python engine did not become healthy in time.')
}

export async function startPythonEngine(opts: { logs: LogBuffer }) {
  const projectRoot = process.cwd()
  const pythonExe = resolvePythonExe(projectRoot)
  const port = await findFreePort()
  const baseUrl = `http://127.0.0.1:${port}`

  const env = {
    ...process.env,
    DAMASCUS_ENGINE_PORT: String(port),
    PYTHONUNBUFFERED: '1'
  }

  const child = spawn(
    pythonExe,
    ['-m', 'uvicorn', 'python.api:app', '--host', '127.0.0.1', '--port', String(port)],
    { cwd: projectRoot, env }
  )

  child.stdout.on('data', (b) => opts.logs.push(b.toString('utf8')))
  child.stderr.on('data', (b) => opts.logs.push(b.toString('utf8')))

  child.on('exit', (code) => {
    opts.logs.push(`[python] exited with code ${code}`)
  })

  await waitForHealth(`${baseUrl}/health`)

  return { baseUrl, port }
}
