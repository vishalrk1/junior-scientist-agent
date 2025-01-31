import React from "react";
import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Step {
  label: string;
  status: "pending" | "loading" | "completed";
}

interface StepProgressProps {
  steps: Step[];
}

export function StepProgress({ steps }: StepProgressProps) {
  return (
    <div className="flex items-center justify-start gap-2">
      {steps.map((step, index) => (
        <React.Fragment key={index}>
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "h-6 w-6 rounded-full flex items-center justify-center",
                step.status === "completed" && "bg-green-500",
                step.status === "loading" && "border-2 border-blue-500",
                step.status === "pending" && "border-2 border-gray-300"
              )}
            >
              {step.status === "completed" ? (
                <Check className="h-4 w-4 text-white" />
              ) : step.status === "loading" ? (
                <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
              ) : (
                <div className="h-4 w-4" />
              )}
            </div>
            <span className="text-sm">{step.label}</span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={cn(
                "h-[2px] w-16",
                step.status === "completed" ? "bg-green-500" : "bg-gray-300"
              )}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
