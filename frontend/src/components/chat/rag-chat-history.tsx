import useRagSession from "@/hooks/useRagSession";
import useRagMessages from "@/hooks/useRagMessages";
import { cn } from "@/lib/utils";
import React from "react";

const RagChatHistory = () => {
  const { currentSession } = useRagSession();
  const { messages } = useRagMessages();

  return (
    <div className="flex-1">
      <div className="flex flex-col space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={cn(
              "flex",
              message.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-lg p-4",
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "dark:bg-card bg-muted",
                "shadow-sm"
              )}
            >
              <p className="text-sm">{message.content}</p>
              {message.source && message.source.length > 0 && (
                <div className="mt-2 text-xs text-muted-foreground">
                  Sources: {message.source.map((s) => s.title).join(", ")}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RagChatHistory;
