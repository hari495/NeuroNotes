import { useState } from 'react'
import { MessageSquare, Layers, Library, Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'
import ThemeToggle from './ThemeToggle'

export default function AppShell({ children, activeView, onViewChange }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'flashcards', label: 'Flashcards', icon: Layers },
    { id: 'library', label: 'Library', icon: Library },
  ]

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="px-6 py-4">
        <h1 className="text-xl font-semibold tracking-tight">NeuroNotes</h1>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeView === item.id
          return (
            <Button
              key={item.id}
              variant="ghost"
              className={`w-full justify-start ${
                isActive ? 'bg-accent' : ''
              }`}
              onClick={() => {
                onViewChange(item.id)
                setSidebarOpen(false)
              }}
            >
              <Icon className="mr-3 h-4 w-4" />
              {item.label}
            </Button>
          )
        })}
      </nav>

      <Separator />

      {/* Footer */}
      <div className="p-4">
        <ThemeToggle />
      </div>
    </div>
  )

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 border-r bg-card md:block">
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <SidebarContent />
        </SheetContent>
      </Sheet>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {/* Mobile Header */}
        <div className="flex items-center gap-2 border-b bg-card px-4 py-3 md:hidden">
          <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
          </Sheet>
          <h1 className="text-lg font-semibold tracking-tight">NeuroNotes</h1>
        </div>

        {/* View Content */}
        <div className="h-full overflow-hidden">{children}</div>
      </main>
    </div>
  )
}
