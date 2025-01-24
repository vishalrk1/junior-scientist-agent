import React from 'react'
import { Textarea } from '../ui/textarea'

const ChatInput = () => {
  return (
    <div className='w-full'>
        <Textarea 
            placeholder='input your text here' 
            className='border-none outline-none focus:outline-none focus:border-none focus-visible:ring-0 shadow-none h-14 text-lg rounded-none'
        />
    </div>
  )
}

export default ChatInput