import useRagSession from "@/hooks/useRagSession";
import useRagMessages from "@/hooks/useRagMessages";
import { cn } from "@/lib/utils";
import React, { useEffect, useRef } from "react";
import { ChevronDown, ChevronUp, BookOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";

const RagChatHistory = () => {
  const { currentSession } = useRagSession();
  const { messages } = useRagMessages();
  const [expandedSources, setExpandedSources] = React.useState<number[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const toggleSource = (index: number) => {
    setExpandedSources((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  return (
    <div className="flex-1 overflow-y-auto">
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
              {message.role === "user" ? (
                <p className="text-sm">{message.content}</p>
              ) : (
                <div className="ai-message">
                  <div className="text-sm prose dark:prose-invert max-w-none">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>

                  {message.source && message.source.length > 0 && (
                    <div className="mt-3 border-t pt-2">
                      <button
                        onClick={() => toggleSource(index)}
                        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors"
                      >
                        <BookOpen size={12} />
                        <span>Sources ({message.source.length})</span>
                        {expandedSources.includes(index) ? (
                          <ChevronUp size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )}
                      </button>

                      {expandedSources.includes(index) && (
                        <div className="grid grid-cols-3 gap-2 mt-2">
                          {message.source.map((source, idx) => (
                            <div
                              key={idx}
                              className="text-xs p-2 rounded bg-muted/50 flex flex-col"
                            >
                              <div className="font-medium line-clamp-1">
                                {source.title}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default RagChatHistory;
