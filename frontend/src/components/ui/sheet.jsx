import * as React from "react"
import { cn } from "@/lib/utils"

const Sheet = ({ children, open, onOpenChange }) => {
  return children
}

const SheetTrigger = React.forwardRef(({ children, asChild, ...props }, ref) => {
  return asChild ? children : <button ref={ref} {...props}>{children}</button>
}
)
SheetTrigger.displayName = "SheetTrigger"

const SheetContent = React.forwardRef(
  ({ className, children, side = "right", ...props }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false)

    // Get the open state from parent Sheet component
    const sheetContext = React.useContext(SheetContext)
    const open = sheetContext?.open ?? isOpen

    React.useEffect(() => {
      if (open) {
        document.body.style.overflow = "hidden"
      } else {
        document.body.style.overflow = ""
      }
      return () => {
        document.body.style.overflow = ""
      }
    }, [open])

    if (!open) return null

    const sideClasses = {
      left: "left-0 top-0 h-full animate-slide-in-from-left",
      right: "right-0 top-0 h-full animate-slide-in-from-right",
      top: "top-0 left-0 w-full animate-slide-in-from-top",
      bottom: "bottom-0 left-0 w-full animate-slide-in-from-bottom",
    }

    return (
      <>
        {/* Backdrop */}
        <div
          className="fixed inset-0 z-50 bg-black/80"
          onClick={() => sheetContext?.onOpenChange?.(false)}
        />

        {/* Sheet content */}
        <div
          ref={ref}
          className={cn(
            "fixed z-50 bg-background shadow-lg transition-all duration-300",
            sideClasses[side],
            className
          )}
          {...props}
        >
          {children}
        </div>
      </>
    )
  }
)
SheetContent.displayName = "SheetContent"

const SheetContext = React.createContext(null)

const SheetProvider = ({ children, open, onOpenChange }) => {
  return (
    <SheetContext.Provider value={{ open, onOpenChange }}>
      {children}
    </SheetContext.Provider>
  )
}

// Wrap the Sheet component to provide context
const SheetWrapper = ({ children, open, onOpenChange }) => {
  return (
    <SheetProvider open={open} onOpenChange={onOpenChange}>
      {children}
    </SheetProvider>
  )
}

export { SheetWrapper as Sheet, SheetTrigger, SheetContent }
