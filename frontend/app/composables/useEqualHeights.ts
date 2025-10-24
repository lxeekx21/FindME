import { onMounted, onBeforeUnmount, nextTick, watch, type WatchSource } from 'vue'
import { useEventListener, useResizeObserver } from '@vueuse/core'
import { watchDebounced } from '@vueuse/shared'

export function useEqualHeights(selectors: string[] | string, watchSource?: WatchSource<unknown>) {
  const classList = Array.isArray(selectors) ? selectors : [selectors]
  const observers: { disconnect: () => void }[] = []

  const equalizeHeights = async () => {
    await nextTick()
    classList.forEach((className) => {
      const elements = Array.from(document.querySelectorAll<HTMLElement>(`.${className}`))
      if (elements.length === 0) return

      // Reset height
      elements.forEach((el) => (el.style.height = 'auto'))

      const max = Math.max(...elements.map((el) => el.offsetHeight))
      elements.forEach((el) => (el.style.height = `${max}px`))
    })
  }

  onMounted(async () => {
    await equalizeHeights()

    // Observe resizes for all matching elements
    classList.forEach((className) => {
      const elements = Array.from(document.querySelectorAll<HTMLElement>(`.${className}`))
      elements.forEach((el) => {
        const { stop } = useResizeObserver(el, equalizeHeights)
        observers.push({ disconnect: stop })
      })
    })

    // Listen to window resize
    useEventListener(window, 'resize', equalizeHeights)

    // Recalculate on reactive source change
    if (watchSource) {
      watchDebounced(
        watchSource,
        async () => {
          await equalizeHeights()
        },
        { debounce: 150, maxWait: 300 }
      )
    }
  })

  onBeforeUnmount(() => {
    observers.forEach((obs) => obs.disconnect())
  })

  return { equalizeHeights }
}
