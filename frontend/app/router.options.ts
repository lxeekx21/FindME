import type { RouterConfig } from '@nuxt/schema'

export default <RouterConfig>{
  scrollBehavior: (to, from, savedPosition) => {
    if (to.hash) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ el: to.hash, behavior: 'smooth', top: 120 })
        }, 200)
      })
    }
    if (to === from) {
      return { left: 0, top: 0, behavior: 'smooth' }
    }
    return savedPosition ? { left: savedPosition.left, top: savedPosition.top } : { left: 0, top: 0 }
  },
}
