import path from 'node:path'
import { Low } from 'lowdb'
import { JSONFile } from 'lowdb/node'

export type UnitSystem = 'metric' | 'imperial'

export type Preferences = {
  unitSystem: UnitSystem
}

const DEFAULTS: Preferences = {
  unitSystem: 'metric'
}

export class PreferencesStore {
  private db: Low<Preferences>

  constructor(userDataPath: string) {
    const file = path.join(userDataPath, 'preferences.json')
    const adapter = new JSONFile<Preferences>(file)
    this.db = new Low(adapter, { ...DEFAULTS })
  }

  private async load() {
    await this.db.read()
    this.db.data ||= { ...DEFAULTS }
  }

  async get(): Promise<Preferences> {
    await this.load()
    return { ...DEFAULTS, ...this.db.data }
  }

  async set(prefs: Partial<Preferences>): Promise<Preferences> {
    await this.load()
    this.db.data = { ...this.db.data!, ...prefs }
    await this.db.write()
    return this.db.data
  }
}
