import * as React from "react";
import { File, MessageCircle } from "lucide-react";

import { Label } from "@/components/ui/label";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Switch } from "@/components/ui/switch";
import useProjects from "@/hooks/useProjects";
import useAuthStore from "@/hooks/useAuthStore";
import { LoginCard } from "../cards/login-card";
import AddProjectButton from "../button/addProject";
import { IconSidebar } from "./icon-sidebar";
import { ProjectList } from "./project-list";

const navItems = [
  {
    title: "Chats",
    url: "#",
    icon: MessageCircle,
    isActive: true,
  },
  {
    title: "Reports",
    url: "#",
    icon: File,
    isActive: false,
  },
];

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const [activeItem, setActiveItem] = React.useState(navItems[0]);
  const { projects, activeProjectId, setActiveProject, fetchProjects, isLoading } = useProjects();
  const { isAuthenticated, user } = useAuthStore();

  // Add effect to fetch projects when authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      fetchProjects();
    }
  }, [isAuthenticated]);

  React.useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash.startsWith("#proj_")) {
        if (!isAuthenticated) {
          window.location.href = "/";
          return;
        }
        setActiveProject(hash.replace("#proj_", ""));
      } else {
        setActiveProject(null);
      }
    };

    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, [setActiveProject, isAuthenticated]);

  return (
    <Sidebar
      collapsible="icon"
      className="overflow-hidden [&>[data-sidebar=sidebar]]:flex-row"
      {...props}
    >
      <IconSidebar 
        navItems={navItems}
        activeItem={activeItem}
        user={user}
        isAuthenticated={isAuthenticated}
      />

      <Sidebar collapsible="none" className="hidden flex-1 md:flex">
        <SidebarHeader className="gap-3.5 border-b p-4">
          <div className="flex w-full items-center justify-between">
            <div className="text-base font-medium text-foreground">
              {activeItem.title}
            </div>
            <Label className="flex items-center gap-2 text-sm">
              <span>Active</span>
              <Switch className="shadow-none" />
            </Label>
          </div>
        </SidebarHeader>
        <SidebarContent className="flex flex-col flex-grow">
          {isAuthenticated ? (
            <>
              <SidebarMenu className="px-0">
                <SidebarMenuItem className="mt-3 mx-2">
                  <AddProjectButton className="w-full" />
                </SidebarMenuItem>
              </SidebarMenu>

              <SidebarGroup className="px-0 flex-grow">
                <SidebarGroupContent>
                  <ProjectList 
                    projects={projects}
                    activeProjectId={activeProjectId}
                    isLoading={isLoading}
                  />
                </SidebarGroupContent>
              </SidebarGroup>
            </>
          ) : (
            <div className="flex-grow flex items-end p-4">
              <LoginCard />
            </div>
          )}
        </SidebarContent>
      </Sidebar>
    </Sidebar>
  );
}
