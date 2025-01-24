import { LucideIcon } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface TooltipIconButtonProps {
  icon: LucideIcon;
  tooltip: string;
  onClick?: () => void;
}

export const TooltipIconButton = ({
  icon: Icon,
  tooltip,
  onClick,
}: TooltipIconButtonProps) => {
  return (
    <Tooltip >
      <TooltipTrigger asChild>
        <div
          className="p-2 rounded-full hover:bg-accent cursor-pointer"
          onClick={onClick}
        >
          <Icon size={24} />
        </div>
      </TooltipTrigger>
      <TooltipContent className="bg-zinc-900 dark:bg-zinc-950 text-zinc-50">
        <span>{tooltip}</span>
      </TooltipContent>
    </Tooltip>
  );
};
