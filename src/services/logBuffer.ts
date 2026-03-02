export class LogBuffer {
  private lines: string[] = []
  constructor(private maxLines = 2000) {}

  push(line: string) {
    const clean = line.replace(/\r?\n$/, '')
    this.lines.push(clean)
    if (this.lines.length > this.maxLines) {
      this.lines.splice(0, this.lines.length - this.maxLines)
    }
  }

  tail(n = 200) {
    return this.lines.slice(Math.max(0, this.lines.length - n))
  }
}
