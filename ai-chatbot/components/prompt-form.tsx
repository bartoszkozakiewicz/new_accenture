'use client'

import * as React from 'react'
import Textarea from 'react-textarea-autosize'

import { axiosInstance } from '@/axiosInstance'
import { UserMessage } from './stocks/message'
import { Button } from '@/components/ui/button'
import { IconArrowElbow, IconPlus } from '@/components/ui/icons'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '@/components/ui/tooltip'
import { useEnterSubmit } from '@/lib/hooks/use-enter-submit'
import { nanoid } from 'nanoid'
import { useRouter } from 'next/navigation'

export function PromptForm({
  input,
  setInput,
  setMessages
}: {
  input: string
  setInput: (value: string) => void
  setMessages: any
}) {
  const router = useRouter()
  const { formRef, onKeyDown } = useEnterSubmit()
  const inputRef = React.useRef<HTMLTextAreaElement>(null)
  const [answearing, setAnswearing] = React.useState(false)

  const handleSendMessage = async () => {
    console.log('send message, fastapi v2', input)
    setMessages((prev: any) => [
      ...prev,
      {
        type: 'User',
        message: input
      }
    ])
    try {
      setAnswearing(true)
      await axiosInstance
        .post(`http://localhost:8000/chat`, {
          message: input
        })
        .then(response => {
          console.log('Response:', response.data.response)
          setMessages((prev: any) => [
            ...prev,
            {
              type: 'Bot',
              message: response.data.response
            }
          ])
        })
        .catch(error => {
          console.log('Error:', error)
        })
        .finally(() => {
          setAnswearing(false)
        })
    } catch (err) {
      console.log('gowno')
    }
  }

  React.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  return (
    <form
      ref={formRef}
      onSubmit={async (e: any) => {
        e.preventDefault()

        // Blur focus on mobile
        if (window.innerWidth < 600) {
          e.target['message']?.blur()
        }

        const value = input.trim()
        setInput('')
        if (!value) return
      }}
    >
      <div className="relative flex max-h-60 w-full grow flex-col overflow-hidden bg-background px-8 sm:rounded-md sm:border sm:px-12">
        <Textarea
          ref={inputRef}
          tabIndex={0}
          onKeyDown={onKeyDown}
          placeholder="Send a message."
          className="min-h-[60px] w-full resize-none bg-transparent px-4 py-[1.3rem] focus-within:outline-none sm:text-sm"
          autoFocus
          spellCheck={false}
          autoComplete="off"
          autoCorrect="off"
          name="message"
          rows={1}
          value={input}
          onChange={e => setInput(e.target.value)}
        />
        <div className="absolute right-0 top-[13px] sm:right-4">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={handleSendMessage}
                type="submit"
                size="icon"
                disabled={input === ''}
              >
                <IconArrowElbow />
                <span className="sr-only">Send message</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>Send message</TooltipContent>
          </Tooltip>
        </div>
      </div>
    </form>
  )
}
