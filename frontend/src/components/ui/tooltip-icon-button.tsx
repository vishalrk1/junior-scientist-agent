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
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className="p-2 rounded-full hover:bg-accent cursor-pointer"
          onClick={onClick}
        >
          <Icon size={24} />
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <span>{tooltip}</span>
      </TooltipContent>
    </Tooltip>
  );
};
