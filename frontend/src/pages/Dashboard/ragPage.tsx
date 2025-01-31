import React from "react";
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

const RagPage = () => {
  const { files } = useFiles();
  const { currentSession, isCreatingSession, isUploadingFiles } =
    useRagSession();

  const steps = [
    {
      label: "Creating Session",
      status: isCreatingSession
        ? "loading"
        : isUploadingFiles || currentSession
        ? "completed"
        : "pending",
    },
    {
      label: "Uploading Files",
      status: isUploadingFiles
        ? "loading"
        : currentSession
        ? "completed"
        : "pending",
    },
  ] as const;

  return (
    <>
      <header className="sticky top-0 flex shrink-0 items-center gap-2 border-b bg-background p-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage className="line-clamp-1 text-lg font-semibold">
                RAG Assistant
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </header>

      <div className="flex flex-1 flex-col gap-4 p-4">
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
      </div>
    </>
  );
};

export default RagPage;
