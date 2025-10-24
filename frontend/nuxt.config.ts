// https://nuxt.com/docs/api/configuration/nuxt-config

import { config as loadEnv } from 'dotenv'
import { resolve } from 'pathe'
loadEnv({ path: `.env` })
import { join } from 'pathe'
import { process } from 'std-env'

export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  future: {
    compatibilityVersion: 4,
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_BASE_API_URL || '',
      googleMapsApiKey: process.env.NUXT_GOOGLE_MAPS_API_KEY,
      googleMapsMapId: process.env.NUXT_GOOGLE_MAPS_MAP_ID,
      mode: process.env.NUXT_ENV_MODE,
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL,
    },
  },
  colorMode: {
    classSuffix: '',
    preference: 'light',
    fallback: 'light',
  },
  ui: {
    fonts: false,
  },
  app: {
    pageTransition: { name: 'page', mode: 'out-in' },
    baseURL: process.env.NUXT_HOME_URL || '/',
    head: {
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
      base: { href: process.env.NUXT_HOME_URL || '/' },
      link: [
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap',
        },
        {
          rel: 'icon',
          type: 'image/x-icon',
          href: '/favicon.ico?v=1',
        },
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      ],
    },
  },
  ssr: false,
  nitro: {
    preset: 'static',
    prerender: {
      crawlLinks: true,
      routes: ['/sitemap.xml'],
    },
  },
  css: ['@/assets/css/main.css'],
  modules: [
    '@nuxt/ui',
    '@nuxtjs/robots',
    '@nuxtjs/sitemap',
    '@nuxtjs/color-mode',
    '@pinia/nuxt',
    'pinia-plugin-persistedstate/nuxt',
    '@nuxt/image',
  ],
})
