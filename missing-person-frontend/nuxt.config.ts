import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default defineNuxtConfig({
  compatibilityDate: '2025-10-21',
  css: [join(__dirname, 'assets', 'css', 'main.css')], // ✅ Windows-safe path join
  modules: ['@nuxtjs/tailwindcss'],
  devtools: { enabled: true },
})
