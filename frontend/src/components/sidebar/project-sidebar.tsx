import { ScrollArea } from "../ui/scroll-area";

import useProjects from "@/hooks/useProjects";
import { ProjectList } from "./project-list";
import { SidebarMenu, SidebarMenuItem } from "../ui/sidebar";
import AddProjectButton from "../button/addProject";

const ProjectSidebar = () => {
  const { projects, activeProjectId, isLoading } = useProjects();

  return (
    <div className="flex h-full flex-col gap-2">
      <SidebarMenu className="px-0">
        <SidebarMenuItem className="mt-3 mx-2">
          <AddProjectButton className="w-full" />
        </SidebarMenuItem>
      </SidebarMenu>
      <ScrollArea className="flex-1">
        <ProjectList
          projects={projects}
          activeProjectId={activeProjectId}
          isLoading={isLoading}
        />
      </ScrollArea>
    </div>
  );
};

export default ProjectSidebar;
