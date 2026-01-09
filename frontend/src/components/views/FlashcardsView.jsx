import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { generateFlashcards } from '@/services/api'

export default function FlashcardsView() {
  const [topic, setTopic] = useState('')
  const [count, setCount] = useState(5)
  const [cards, setCards] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [sources, setSources] = useState([])
  const [reverseMode, setReverseMode] = useState(false)

  const handleGenerate = async () => {
    if (!topic.trim()) return

    setIsLoading(true)
    try {
      const response = await generateFlashcards(topic, count)
      setCards(response.cards)
      setSources(response.context_sources || [])
      setCurrentIndex(0)
      setIsFlipped(false)
    } catch (error) {
      console.error('Flashcard generation failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNext = () => {
    // Cycle back to beginning when at the end
    setCurrentIndex((currentIndex + 1) % cards.length)
    setIsFlipped(false)
  }

  const handlePrev = () => {
    // Cycle to end when at the beginning
    setCurrentIndex((currentIndex - 1 + cards.length) % cards.length)
    setIsFlipped(false)
  }

  const handleFlip = () => setIsFlipped(!isFlipped)

  const handleKeyPress = (e) => {
    if (cards.length === 0) return
    if (e.key === ' ') {
      e.preventDefault()
      handleFlip()
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      handleNext()
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      handlePrev()
    }
  }

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [cards, currentIndex, isFlipped])

  if (cards.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Card className="w-full max-w-md space-y-6 p-6">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Generate Flashcards</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Create study flashcards from your notes
            </p>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="topic">Topic</Label>
              <Input
                id="topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., linear algebra, photosynthesis"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="count">Number of cards</Label>
              <select
                id="count"
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>

            <Button
              className="w-full"
              onClick={handleGenerate}
              disabled={isLoading}
            >
              {isLoading ? 'Generating...' : 'Generate Flashcards'}
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  const currentCard = cards[currentIndex]

  // Determine what to show on front and back based on reverse mode
  const frontContent = reverseMode ? currentCard.back : currentCard.front
  const backContent = reverseMode ? currentCard.front : currentCard.back

  return (
    <div className="flex h-full flex-col items-center justify-center p-6">
      {/* Progress Badge */}
      <div className="mb-6 flex items-center gap-3">
        <Badge variant="secondary">
          Card {currentIndex + 1} of {cards.length}
        </Badge>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setReverseMode(!reverseMode)}
          className="gap-2"
        >
          <RotateCcw className="h-3 w-3" />
          {reverseMode ? 'Answer by Definition' : 'Answer by Term'}
        </Button>
      </div>

      {/* Flashcard */}
      <div className="perspective-1000 mb-8">
        <motion.div
          key={currentIndex} // Force remount on card change to prevent flip animation
          className="relative h-[350px] w-[600px] max-w-full cursor-pointer"
          onClick={handleFlip}
          initial={{ rotateY: 0 }}
          animate={{ rotateY: isFlipped ? 180 : 0 }}
          transition={{ duration: 0.6, type: 'spring', stiffness: 100 }}
          style={{
            transformStyle: 'preserve-3d',
          }}
        >
          {/* Front */}
          <Card
            className="absolute inset-0 flex items-center justify-center border p-12 text-center shadow-sm"
            style={{
              backfaceVisibility: 'hidden',
            }}
          >
            <div>
              <p className="text-3xl font-serif">{frontContent}</p>
              <p className="mt-4 text-xs text-muted-foreground">Click to flip</p>
            </div>
          </Card>

          {/* Back */}
          <Card
            className="absolute inset-0 flex items-center justify-center border p-12 text-center shadow-sm"
            style={{
              backfaceVisibility: 'hidden',
              transform: 'rotateY(180deg)',
            }}
          >
            <p className="text-lg leading-relaxed">{backContent}</p>
          </Card>
        </motion.div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="icon"
          onClick={handlePrev}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <Button onClick={handleFlip}>
          Flip
        </Button>

        <Button
          variant="outline"
          size="icon"
          onClick={handleNext}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2">
          <span className="text-sm text-muted-foreground">Sources:</span>
          {sources.map((source, i) => (
            <Badge key={i} variant="outline" className="text-xs">
              {source}
            </Badge>
          ))}
        </div>
      )}

      {/* Reset */}
      <Button
        variant="ghost"
        className="mt-6"
        onClick={() => setCards([])}
      >
        Generate New Set
      </Button>

      {/* Keyboard Hints */}
      <p className="mt-4 text-xs text-muted-foreground">
        💡 Use ← → to navigate (cycles), Space to flip
      </p>
    </div>
  )
}
