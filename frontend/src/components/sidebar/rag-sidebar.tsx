import { Button } from "../ui/button";
import { Upload } from "lucide-react";
import { ScrollArea } from "../ui/scroll-area";
import { cn } from "@/lib/utils";

const RagSidebar = () => {
  return (
    <div className="flex h-full w-full flex-col gap-2">
      <Button
        type="button"
        className={cn(
          "flex items-center gap-2 px-4 py-2 m-2",
          "hover:bg-slate-100 dark:hover:bg-slate-800",
          "transition-colors duration-200"
        )}
        variant="outline"
      >
        <Upload className="h-4 w-4" />
        <span className="text-sm">Upload Documents</span>
      </Button>
      <ScrollArea className="flex-1"></ScrollArea>
    </div>
  );
};

export default RagSidebar;
