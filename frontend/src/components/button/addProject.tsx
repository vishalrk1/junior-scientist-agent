import React, { useState } from "react";
import { Button } from "../ui/button";
import { Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "../ui/dialog";
import { cn } from "@/lib/utils";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { ModelProviders } from "@/lib/types";
import { Textarea } from "../ui/textarea";
import { Separator } from "../ui/separator";
import { AnimatePresence, motion } from "framer-motion";

interface AddProjectButtonProps {
  className?: string;
}

const AddProjectButton = ({ className }: AddProjectButtonProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    modelProvider: "",
    apiKey: "",
  });

  const isFormValid = formData.name && formData.modelProvider && formData.apiKey;

  const handleCreate = () => {
    if (isFormValid) {
      console.log("Creating project:", formData);
      setIsOpen(false);
      setFormData({ name: "", description: "", modelProvider: "", apiKey: "" });
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          type="button"
          onClick={() => setIsOpen(true)}
          className={cn(
            "flex items-center gap-2 px-4 py-2",
            "hover:bg-slate-100 dark:hover:bg-slate-800",
            "transition-colors duration-200",
            className
          )}
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          <span className="text-sm">Add New Project</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader className="space-y-3">
          <DialogTitle className="text-2xl font-semibold">Add New Project</DialogTitle>
          <DialogDescription>
            Create a new project by filling out the information below. You'll need an API key from your chosen model provider.
          </DialogDescription>
        </DialogHeader>
        <Separator className="my-4" />
        <div className="grid gap-6 py-4">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium">
                Project Name<span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter project name"
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm font-medium">
                Description
              </Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Enter project description"
                className="min-h-[100px] w-full"
              />
            </div>
          </div>

          <Separator className="my-2" />

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="model-provider" className="text-sm font-medium">
                Model Provider<span className="text-red-500">*</span>
              </Label>
              <Select
                value={formData.modelProvider}
                onValueChange={(value) => setFormData({ ...formData, modelProvider: value, apiKey: "" })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a model provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ModelProviders.OpenAI} className="cursor-pointer">
                    OpenAI
                  </SelectItem>
                  <SelectItem value={ModelProviders.Gemini} className="cursor-pointer">
                    Gemini
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <AnimatePresence>
              {formData.modelProvider && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-2"
                >
                  <div className="space-y-2">
                    <Label htmlFor="api-key" className="text-sm font-medium flex items-center justify-between">
                      <span>
                        API Key<span className="text-red-500">*</span>
                      </span>
                      <span className="text-xs text-muted-foreground">
                        For {formData.modelProvider === ModelProviders.OpenAI ? 'OpenAI' : 'Gemini'} API
                      </span>
                    </Label>
                    <Input
                      id="api-key"
                      type="password"
                      value={formData.apiKey}
                      onChange={(e) => setFormData({ ...formData, apiKey: e.target.value })}
                      placeholder={`Enter your ${formData.modelProvider} API key`}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      Your API key will be encrypted and stored securely
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
        <Separator className="my-4" />
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={() => setIsOpen(false)}
            className="px-6"
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!isFormValid}
            className="px-6"
          >
            Create Project
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AddProjectButton;
