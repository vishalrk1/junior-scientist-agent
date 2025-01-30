import { create } from 'zustand'
import { MessageCircle, File } from 'lucide-react'

export const navItems = [
  {
    title: "Data Buddy",
    url: "/dashboard",
    icon: MessageCircle,
    isActive: true,
  },
  {
    title: "Chat with PDF",
    url: "/rag",
    icon: File,
    isActive: false,
  },
] as const

type NavStore = {
  activeItem: typeof navItems[number]
  setActiveItem: (url: string) => void
}

const useNavStore = create<NavStore>((set) => ({
  activeItem: navItems[0],
  setActiveItem: (url) =>
    set(() => ({
      activeItem: navItems.find((item) => item.url === url) || navItems[0],
    })),
}))

export default useNavStore
