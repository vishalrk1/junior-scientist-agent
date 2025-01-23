import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Folder, Globe, Plus, Settings, Settings2, Star } from "lucide-react";
import useProjects from "@/hooks/useProjects";

import React from "react";
import { formatDate } from "@/utils/formater";
import ChatInput from "@/components/textbox/chatInput";
import { TooltipProvider } from "@/components/ui/tooltip";
import { TooltipIconButton } from "@/components/ui/tooltip-icon-button";
import { Project } from "@/lib/types";
import AddProjectButton from "@/components/button/addProject";

const CHAT_ACTIONS = [
  { icon: Folder, tooltip: "Upload Files" },
  { icon: Globe, tooltip: "Web Browsing" },
  { icon: Settings2, tooltip: "Context settings" },
];

const HeaderActions = ({
  activeProject,
}: {
  activeProject: Project | null;
}) => (
  <div className="ml-auto px-3">
    <div className="flex items-center gap-2 text-sm">
      <div className="hidden font-medium text-muted-foreground md:inline-block">
        {activeProject &&
          (activeProject?.updated_at
            ? `Edit ${formatDate(activeProject.updated_at)}`
            : `Created ${formatDate(activeProject.created_at)}`)}
      </div>
      <Button variant="ghost" size="icon" className="h-7 w-7">
        <Star />
      </Button>
      <Separator orientation="vertical" className="mr-2 h-4" />
      <Button variant="ghost" size="icon" className="h-7 w-7">
        <Settings />
      </Button>
    </div>
  </div>
);

const Dashboard = () => {
  const { activeProjectId, getActiveProject } = useProjects();
  const activeProject = getActiveProject();

  console.log(activeProjectId)

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "350px",
        } as React.CSSProperties
      }
    >
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 flex shrink-0 items-center gap-2 border-b bg-background p-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage className="line-clamp-1 text-lg font-semibold">
                  {activeProject?.name}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <HeaderActions activeProject={activeProject} />
        </header>
        <div className="flex flex-1 flex-col gap-4 p-4">
          {!activeProjectId && (
            <div className="flex flex-col items-center justify-center gap-4 w-full h-full">
              <div className="flex flex-col items-center gap-2">
                <div className="flex gap-3 items-center justify-center">
                  <div className="rounded-full bg-primary/10 p-3">
                    <Settings2 className="h-6 w-6 text-primary" />
                  </div>
                  <h1 className="text-4xl font-bold text-primary">
                    Data Buddy
                  </h1>
                </div>
                <p className="text-lg text-center text-muted-foreground max-w-md">
                  Meet your junior data scientist and start working on your base
                  models
                </p>
              </div>
              <AddProjectButton />
            </div>
          )}
        </div>
        <div className="flex flex-col gap-1 border-t border-border p-4">
          <div className="flex items-center justify-start bg-background mx-2 gap-1">
            <TooltipProvider delayDuration={200}>
              {CHAT_ACTIONS.map((action, index) => (
                <TooltipIconButton
                  key={index}
                  icon={action.icon}
                  tooltip={action.tooltip}
                />
              ))}
            </TooltipProvider>
          </div>
          <ChatInput />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
};

export default Dashboard;
