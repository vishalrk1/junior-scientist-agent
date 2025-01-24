import React, { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { Settings, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Separator } from "../ui/separator";
import useProjects from "@/hooks/useProjects";
import { ProjectSettings, ProjectStatus } from "@/lib/types";
import { Badge } from "../ui/badge";

const StatusBadge = ({ status }: { status: ProjectStatus }) => {
  const statusColors = {
    [ProjectStatus.active]: "bg-green-500",
    [ProjectStatus.archived]: "bg-yellow-500",
    [ProjectStatus.deleted]: "bg-red-500",
  };

  return (
    <Badge variant="secondary" className="gap-2 mt-1">
      <div className={`h-2 w-2 rounded-full ${statusColors[status]}`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
};

const SettingsButton = () => {
  const { getActiveProject, updateProject, deleteProject } = useProjects();
  const activeProject = getActiveProject();
  const [isOpen, setIsOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    settings: {
      context_size: 4096,
      max_reports_per_agent: 5,
      auto_save_interval: 300,
      selected_model: "",
    },
  });

  useEffect(() => {
    if (activeProject && isOpen) {
      setFormData({
        name: activeProject.name,
        description: activeProject.description || "",
        settings: {
          context_size: activeProject.settings?.context_size || 4096,
          max_reports_per_agent:
            activeProject.settings?.max_reports_per_agent || 5,
          auto_save_interval: activeProject.settings?.auto_save_interval || 300,
          selected_model: activeProject.settings?.selected_model || "",
        },
      });
    }
  }, [activeProject, isOpen]);

  if (!activeProject) return null;

  const handleSave = async () => {
    if (!activeProject?.id) return;

    setIsSaving(true);
    try {
      await updateProject(activeProject.id, {
        name: formData.name,
        description: formData.description,
        settings: formData.settings as ProjectSettings,
      });
      setIsOpen(false);
    } catch (error) {
      console.error("Failed to update project:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!activeProject?.id) return;
    setIsOpen(false);
    setIsDeleting(true);
    try {
      await deleteProject(activeProject.id);
      setIsDeleteDialogOpen(false);
      setIsOpen(false);
      // Clear the project ID from URL
      window.location.hash = '';
    } catch (error) {
      console.error("Failed to delete project:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon" className="h-7 w-7">
            <Settings />
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto custom-scrollbar">
          <DialogHeader className="">
            <div className="flex items-center justify-start gap-2">
              <DialogTitle className="text-xl font-semibold">
                Project Settings
              </DialogTitle>
              <StatusBadge status={activeProject.status} />
            </div>
            <DialogDescription>
              Configure project settings and preferences.
            </DialogDescription>
          </DialogHeader>
          <Separator />
          <div className="grid gap-6">
            <div className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="name" className="text-sm font-medium">
                  Project Name<span className="text-red-500">*</span>
                </Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder="Enter project name"
                  className="w-full"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="description" className="text-sm font-medium">
                  Description
                </Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="Enter project description"
                  className="min-h-[100px] w-full"
                />
              </div>
              <Separator />
              <div className="grid gap-4 grid-cols-2">
                <div className="space-y-1">
                  <Label htmlFor="description" className="text-sm font-medium">
                    Max Reports per Agent
                  </Label>
                  <Input
                    id="max_reports"
                    type="number"
                    value={formData.settings.max_reports_per_agent}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        settings: {
                          ...formData.settings,
                          max_reports_per_agent: parseInt(e.target.value),
                        },
                      })
                    }
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="auto_save">
                    Auto-save Interval (seconds)
                  </Label>
                  <Input
                    id="auto_save"
                    type="number"
                    value={formData.settings.auto_save_interval}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        settings: {
                          ...formData.settings,
                          auto_save_interval: parseInt(e.target.value),
                        },
                      })
                    }
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center gap-3 mt-6">
            <Button
              variant="destructive"
              onClick={() => setIsDeleteDialogOpen(true)}
              className="flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Delete Project
            </Button>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Project</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{activeProject.name}"? This
              action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete Project"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default SettingsButton;
