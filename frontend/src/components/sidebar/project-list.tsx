
import * as React from "react";
import { formatDate } from "@/utils/formater";
import { Project } from "@/lib/types";

interface ProjectListProps {
  projects: Project[];
  activeProjectId: string | null;
  isLoading: boolean;
}

export function ProjectList({ projects, activeProjectId, isLoading }: ProjectListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <span className="text-sm text-muted-foreground">Loading projects...</span>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-4 gap-2">
        <span className="text-sm text-muted-foreground">No projects yet</span>
        <span className="text-xs text-muted-foreground">Create your first project to get started</span>
      </div>
    );
  }

  return (
    <>
      {projects.map((project) => (
        <a
          href={`#proj_${project.id}`}
          key={project.id}
          className={`flex flex-col items-start gap-1 px-4 py-3 text-sm leading-tight transition-colors ${
            project.id === activeProjectId
              ? "bg-sidebar-accent text-sidebar-accent-foreground"
              : "border-b last:border-b-0 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
          }`}
        >
          <div className="flex w-full items-center gap-2">
            <span className="font-semibold">{project.name}</span>
            <span className="ml-auto text-xs">
              {formatDate(project.created_at)}
            </span>
          </div>
          <span className="line-clamp-2 w-full whitespace-break-spaces text-xs">
            {project?.description}
          </span>
        </a>
      ))}
    </>
  );
}