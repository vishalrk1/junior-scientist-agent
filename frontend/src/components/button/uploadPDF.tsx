import React, { useState, useCallback } from "react";
import { Button } from "../ui/button";
import { cn } from "@/lib/utils";
import { Upload, X, FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import { Progress } from "../ui/progress";
import { useDropzone } from "react-dropzone";
import useFiles from "@/hooks/useFiles";
import useRagSession from "@/hooks/useRagSession";
import useAuthStore from "@/hooks/useAuthStore";
import { Separator } from "../ui/separator";
import { Label } from "../ui/label";
import { Input } from "../ui/input";

interface UploadPDFButtonProps {
  className?: string;
}

const UploadPDFButton: React.FC<UploadPDFButtonProps> = ({ className }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const { user } = useAuthStore();
  const { files, maxFiles, addFiles, removeFile } = useFiles();

  const { createSession, uploadFiles } = useRagSession();

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      addFiles(acceptedFiles);
    },
    [addFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
    },
    maxFiles: maxFiles,
  });

  const handleSubmit = async () => {
    try {
        setIsOpen(false);
        if (user && files.length > 0) {
            const session = await createSession(
            user?.id,
            apiKey,
            `Document Analysis Session ${new Date().toLocaleString()}`,
            "Created from document upload"
            );
            await uploadFiles(session.id, files);
        } else {
            setIsOpen(true);
            throw new Error("User not authenticated or no files to upload");
        }
    } catch (error) {
      console.error("Error during upload process:", error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          type="button"
          className={cn(
            "flex items-center gap-2 px-4 py-2 m-2",
            "hover:bg-slate-100 dark:hover:bg-slate-800",
            "transition-colors duration-200",
            className
          )}
          variant="outline"
          onClick={() => setIsOpen(true)}
        >
          <Upload className="h-4 w-4" />
          <span className="text-sm">Upload Documents</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[550px] max-h-[95vh] overflow-y-auto custom-scrollbar pr-6">
        <DialogHeader className="">
          <DialogTitle className="text-2xl font-semibold">
            Upload Data files
          </DialogTitle>
          <DialogDescription>
            Upload up to 5 PDF or text files to extract information from them.
          </DialogDescription>
        </DialogHeader>

        <Separator className="my-0 py-0" />
        <div className="space-y-1">
          <Label
            htmlFor="api-key"
            className="text-sm font-medium flex items-center justify-between"
          >
            <span>
              API Key<span className="text-red-500">*</span>
            </span>
            <span className="text-xs text-muted-foreground">
              For OpenAI API
            </span>
          </Label>
          <Input
            id="api-key"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={`Enter your openAI API key`}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground">
            Your API key will be encrypted and stored securely
          </p>
        </div>

        <div className="space-y-4 mt-4">
          <div
            {...getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer",
              "transition-colors duration-200",
              isDragActive ? "border-primary bg-primary/5" : "border-muted"
            )}
          >
            <input {...getInputProps()} />
            <Upload className="h-8 w-8 mx-auto mb-4 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Drag & drop files here, or click to select files
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Upload progress</span>
              <span>
                {files.length}/{maxFiles} files
              </span>
            </div>
            <Progress value={(files.length / maxFiles) * 100} />
          </div>
          {files.length > 0 && (
            <div className="grid grid-cols-2 gap-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between px-3 py-2 bg-muted rounded"
                >
                  <div className="flex items-center gap-2 overflow-hidden">
                    <FileText className="h-4 w-4 flex-shrink-0" />
                    <span className="text-sm truncate">{file.name}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    className="flex-shrink-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>Submit</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UploadPDFButton;
