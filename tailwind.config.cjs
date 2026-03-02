module.exports = {
  content: [
    "./src/renderer/index.html",
    "./src/renderer/src/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      boxShadow: {
        glow: "0 0 0 1px rgba(255,255,255,0.08), 0 10px 30px rgba(0,0,0,0.35)"
      }
    }
  },
  plugins: []
}
