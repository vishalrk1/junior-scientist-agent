import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import useRagSession from "@/hooks/useRagSession";
import { FileText } from "lucide-react";
import { StepProgress } from "@/components/ui/step-progress";
import useFiles from "@/hooks/useFiles";
import RagChatHistory from "@/components/chat/rag-chat-history";
import useRagMessages from "@/hooks/useRagMessages";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Loader2, Send } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import RagSessionList from "@/components/sidebar/rag/rag-list";

const RagPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { files } = useFiles();
  const {
    currentSession,
    isUploadingFiles,
    fetchSession,
    fetchSessions,
    isLoading: isSessionLoading,
  } = useRagSession();
  const {
    addUserMessage,
    addAiMessage,
    isLoading: isMessageLoading,
    error,
  } = useRagMessages();
  const [message, setMessage] = useState("");
  const [inputError, setInputError] = useState("");

  useEffect(() => {
    const sessionId = location.hash.slice(1);
    if (sessionId) {
      fetchSession(sessionId).catch(() => {
        navigate("/rag");
      });
    } else {
      navigate("/rag");
    }
  }, [location.hash]);

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim()) {
      setInputError("Please enter a message");
      return;
    }
    if (!currentSession?.id) {
      setInputError("No active session");
      return;
    }

    setInputError("");

    try {
      addUserMessage(message);
      await addAiMessage(message, currentSession.id);
      setMessage("");
    } catch (err) {
      setInputError("Failed to send message. Please try again.");
    }
  };

  const steps = [
    {
      label: "Loading Session",
      status: isSessionLoading
        ? "loading"
        : currentSession
        ? "completed"
        : "pending",
    },
    {
      label: "Processing Files",
      status: isUploadingFiles
        ? "loading"
        : currentSession?.documents?.length
        ? "completed"
        : "pending",
    },
  ] as const;

  if (isSessionLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!currentSession) {
    return null;
  }

  return (
    <div className="flex flex-col h-screen">
      <header className="sticky top-0 flex shrink-0 items-center gap-2 border-b bg-background p-3.5">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage className="line-clamp-1 text-lg font-semibold">
                {currentSession?.title || "RAG Assistant"}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </header>

      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          <div className="border rounded-lg p-4 bg-card">
            <h2 className="text-lg font-semibold mb-4">Uploaded Documents</h2>
            <div className="flex gap-8">
              <div className="flex-1">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  {files &&
                    files.map((file, index) => (
                      <div
                        key={index}
                        className="flex flex-col items-center p-4 border rounded-lg hover:shadow-md transition-shadow bg-white dark:bg-gray-800"
                      >
                        <div className="w-16 h-16 flex items-center justify-center mb-2">
                          <FileText className="w-12 h-12 text-blue-500" />
                        </div>
                        <span className="text-sm text-center break-words w-full">
                          {file.name}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
            <div className="shrink-0 items-start mt-4">
              <StepProgress steps={steps} />
            </div>
          </div>

          {error && (
            <Alert variant="destructive" className="mx-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <RagChatHistory />
        </div>

        <form onSubmit={handleSubmit} className="border-t bg-background p-4">
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <Textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message here..."
                className="border-none outline-none focus:outline-none focus:border-none focus-visible:ring-0 shadow-none h-14 text-lg rounded-none"
                disabled={isMessageLoading || !currentSession}
              />
              {inputError && (
                <p className="text-sm text-destructive mt-1">{inputError}</p>
              )}
            </div>
            <Button
              type="submit"
              disabled={isMessageLoading || !currentSession || !message.trim()}
              className="h-14 px-6"
            >
              {isMessageLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RagPage;
