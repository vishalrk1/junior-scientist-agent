import { RagSession } from "@/lib/types";
import { formatDate } from "@/utils/formater";

interface RagSessionListProps {
  ragSessionList: RagSession[];
  activeRagId: string | undefined;
  isLoading: boolean;
}

const RagSessionList: React.FC<RagSessionListProps> = ({
  activeRagId,
  isLoading,
  ragSessionList,
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <span className="text-sm text-muted-foreground">
          Loading Sessions ...
        </span>
      </div>
    );
  }

  if (ragSessionList.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-4 gap-2">
        <span className="text-sm text-muted-foreground">
          No history available
        </span>
      </div>
    );
  }

  return (
    <>
      {ragSessionList.map((rag) => (
        <a
          href={`#${rag.id}`}
          key={rag.id}
          className={`flex flex-col items-start gap-1 px-4 py-3 text-sm leading-tight transition-colors ${
            rag.id === activeRagId
              ? "bg-sidebar-accent text-sidebar-accent-foreground"
              : "border-b last:border-b-0 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
          }`}
        >
          <div className="flex w-full items-center gap-2">
            <span className="font-semibold min-w-0 flex-1 truncate">
              Rag Title
            </span>
            <span className="ml-auto text-xs shrink-0">
              {formatDate(rag.created_at)}
            </span>
          </div>
          <span className="line-clamp-2 w-full whitespace-break-spaces text-xs">
            {rag?.description}
          </span>
        </a>
      ))}
    </>
  );
};

export default RagSessionList;
