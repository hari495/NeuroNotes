import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useEffect, useState } from 'react'

export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => {
    // Initialize from body class
    if (typeof window !== 'undefined') {
      return document.body.classList.contains('dark') ? 'dark' : 'light'
    }
    return 'dark'
  })

  useEffect(() => {
    const body = document.body
    const root = document.documentElement

    // Remove both classes first
    body.classList.remove('light', 'dark')
    root.classList.remove('light', 'dark')

    // Add the current theme
    body.classList.add(theme)
    root.classList.add(theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark')
  }

  return (
    <Button variant="outline" size="sm" onClick={toggleTheme} className="w-full">
      {theme === 'dark' ? (
        <>
          <Sun className="mr-2 h-4 w-4" />
          Light Mode
        </>
      ) : (
        <>
          <Moon className="mr-2 h-4 w-4" />
          Dark Mode
        </>
      )}
    </Button>
  )
}
