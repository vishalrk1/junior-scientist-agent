import { ScrollArea } from "../ui/scroll-area";
import UploadPDFButton from "../button/uploadPDF";

const RagSidebar = () => {
  return (
    <div className="flex h-full w-full flex-col gap-2">
      <UploadPDFButton />
      <ScrollArea className="flex-1"></ScrollArea>
    </div>
  );
};

export default RagSidebar;
