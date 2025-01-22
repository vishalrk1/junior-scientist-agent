import React from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

const ChatSection = () => {
  return (
    <div className="flex h-full flex-col bg-zinc-900 w-full">
      {/* Navbar */}
      <div className="border-b border-border/10 p-4 dark:bg-zinc-800/50">
        <h1 className="text-xl font-semibold text-zinc-200 pl-12 md:pl-0">Project 1</h1>
      </div>
      <div className="flex-1 overflow-y-auto p-4 dark:bg-zinc-900">
        {/* Messages will go here */}
      </div>

      <div className="border-t border-border/50 p-4 dark:bg-zinc-800/50">
        <form 
          className="flex gap-2 max-w-5xl mx-auto"
          onSubmit={(e) => {
            e.preventDefault()
            // Handle message submit
          }}
        >
          <Textarea 
            placeholder="Type your message..." 
            className="min-h-[44px] max-h-[200px] resize-none flex-1 dark:bg-zinc-800 dark:text-white dark:border-zinc-700"
          />
          <Button type="submit" size="icon" className="dark:bg-zinc-700 dark:hover:bg-zinc-600">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}

export default ChatSection
