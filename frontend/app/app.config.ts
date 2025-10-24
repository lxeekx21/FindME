export default defineAppConfig({
  ui: {
    radius: 'none',
    colors: {
      // Use the new primary palette (see main.css --color-primary-*)
      primary: 'primary',
      secondary: 'indigo',
      // Keep fs as neutral (slate-like) for surfaces and layout
      neutral: 'fs',
    },
    button: {
      slots: {
        base: ['cursor-pointer'],
      },
    },
  },
})
