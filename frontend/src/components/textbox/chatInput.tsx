import React from 'react'
import { Textarea } from '../ui/textarea'

const ChatInput = () => {
  return (
    <div className='w-full'>
        <Textarea placeholder='input your text here' className='border-none active:border-none rounded-none'/>
    </div>
  )
}

export default ChatInput