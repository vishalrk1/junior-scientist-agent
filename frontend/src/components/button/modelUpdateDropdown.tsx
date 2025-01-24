import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Project } from "@/lib/types";
import useProjects from "@/hooks/useProjects";

interface ModelUpdateDropdownProps {
  activeProject: Project;
}

const ModelUpdateDropdown: React.FC<ModelUpdateDropdownProps> = ({
  activeProject,
}) => {
  const { updateProject } = useProjects();

  const handleModelChange = async (model: string) => {
    try {
      await updateProject(activeProject.id, {
        settings: {
          ...activeProject.settings,
          selected_model: model
        }
      });
    } catch (error) {
      console.error('Failed to update model:', error);
    }
  };

  return (
    <Select 
      defaultValue={activeProject?.settings?.selected_model}
      onValueChange={handleModelChange}
    >
      <SelectTrigger className="w-max border-none focus:ring-0 focus:ring-offset-0">
        <SelectValue
          placeholder="Select model"
          defaultValue={activeProject?.settings?.selected_model}
        />
      </SelectTrigger>
      <SelectContent>
        {activeProject?.available_models.map((model) => (
          <SelectItem key={model} value={model} className="cursor-pointer">
            <span className="mx-2">{model}</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default ModelUpdateDropdown;
