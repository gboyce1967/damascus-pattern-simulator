import path from 'node:path'
import { Low } from 'lowdb'
import { JSONFile } from 'lowdb/node'
import crypto from 'node:crypto'

type Project = {
  id: string
  name: string
  createdAt: string
  updatedAt: string
  engineConfig: any
  operations: any[]
}

type DbShape = { projects: Project[] }

export class ProjectStore {
  private db: Low<DbShape>

  constructor(userDataPath: string) {
    const file = path.join(userDataPath, 'projects.json')
    const adapter = new JSONFile<DbShape>(file)
    this.db = new Low(adapter, { projects: [] })
  }

  private async load() {
    await this.db.read()
    this.db.data ||= { projects: [] }
  }

  async list() {
    await this.load()
    return this.db.data!.projects
  }

  async save(project: Partial<Project>) {
    await this.load()
    const now = new Date().toISOString()

    const id = project.id || crypto.randomUUID()
    const existing = this.db.data!.projects.find(p => p.id === id)

    const merged: Project = {
      id,
      name: project.name || existing?.name || 'Untitled Project',
      createdAt: existing?.createdAt || now,
      updatedAt: now,
      engineConfig: project.engineConfig ?? existing?.engineConfig ?? {},
      operations: project.operations ?? existing?.operations ?? []
    }

    this.db.data!.projects = [
      ...this.db.data!.projects.filter(p => p.id !== id),
      merged
    ]

    await this.db.write()
    return merged
  }

  async remove(id: string) {
    await this.load()
    this.db.data!.projects = this.db.data!.projects.filter(p => p.id !== id)
    await this.db.write()
    return { ok: true }
  }
}
