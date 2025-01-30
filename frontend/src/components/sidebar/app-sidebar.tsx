import * as React from "react";
import { useLocation } from "react-router-dom";
import { Label } from "@/components/ui/label";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { Switch } from "@/components/ui/switch";
import useProjects from "@/hooks/useProjects";
import useAuthStore from "@/hooks/useAuthStore";
import useNavStore, { navItems } from "@/store/useNavStore";
import { IconSidebar } from "./icon-sidebar";
import RagSidebar from "./rag-sidebar";
import ProjectSidebar from "./project-sidebar";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();
  const { activeItem } = useNavStore();
  const { setActiveProject, fetchProjects } = useProjects();
  const { isAuthenticated, user } = useAuthStore();

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
          {location.pathname === "/rag" ? (
            <RagSidebar />
          ) : (
            <ProjectSidebar />
          )}
        </SidebarContent>
      </Sidebar>
    </Sidebar>
  );
}
