import React from 'react'
import { Plus } from 'lucide-react'
import { 
  Sidebar, 
  SidebarContent, 
  SidebarHeader, 
  SidebarProvider, 
  SidebarTrigger,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton
} from '@/components/ui/sidebar'
import { Button } from '@/components/ui/button'
import ChatSection from '@/components/chat/chat-section'
import { CreateProjectDialog } from '@/components/project/create-project-dialog'

const Dashboard = () => {
  const [showProjectModal, setShowProjectModal] = React.useState(false)

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex h-screen bg-zinc-900">
        <Sidebar className="border-r border-border/50">
          <SidebarHeader className="border-b border-border/50">
            <div className="flex items-center justify-between px-2">
              <h2 className="text-lg font-semibold">Projects</h2>
              <SidebarTrigger />
            </div>
          </SidebarHeader>
          <SidebarContent>
            <div className="p-2">
              <Button 
                className="w-full justify-start gap-2" 
                onClick={() => setShowProjectModal(true)}
              >
                <Plus className="h-4 w-4" />
                Create Project
              </Button>
            </div>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton>Project 1</SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton>Project 2</SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarContent>
        </Sidebar>

        <div className="flex-1 relative">
          {/* Mobile sidebar trigger */}
          <div className="absolute left-4 top-4 md:hidden z-50">
            <SidebarTrigger />
          </div>
          <ChatSection />
        </div>

        <CreateProjectDialog 
          open={showProjectModal} 
          onOpenChange={setShowProjectModal} 
        />
      </div>
    </SidebarProvider>
  )
}

export default Dashboard