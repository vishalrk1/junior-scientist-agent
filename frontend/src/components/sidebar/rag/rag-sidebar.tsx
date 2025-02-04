import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarMenu, SidebarMenuItem } from "@/components/ui/sidebar";
import RagSessionList from "./rag-list";
import useRagSession from "@/hooks/useRagSession";
import UploadPDFButton from "@/components/button/uploadPDF";

const RagSidebar = () => {
  const { currentSession, sessions } = useRagSession();

  return (
    <div className="flex h-full flex-col gap-2">
      <SidebarMenu className="px-0">
        <SidebarMenuItem className="mt-3 mx-2">
          <UploadPDFButton className="w-full" />
        </SidebarMenuItem>
      </SidebarMenu>
      <ScrollArea className="flex-1">
        <RagSessionList
          ragSessionList={sessions}
          activeRagId={currentSession?.id}
          isLoading={false}
        />
      </ScrollArea>
    </div>
  );
};

export default RagSidebar;
