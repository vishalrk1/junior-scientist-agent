import { ScrollArea } from '@/components/ui/scroll-area'
import { useChat } from '@/hooks/useChat'
import { cn } from '@/lib/utils'
import { Loader2, User, Bot, LineChart, Brain, Lightbulb, Upload } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { useEffect, useRef, useState } from 'react'
import { Input } from '@/components/ui/input'
import useProjects from '@/hooks/useProjects'
import useAuthStore from '@/hooks/useAuthStore'
import { Progress } from "@/components/ui/progress";

const AgentIcon = ({ type }: { type: string }) => {
  switch (type) {
    case 'analyzer':
      return <LineChart className="h-4 w-4" />
    case 'advisor':
      return <Brain className="h-4 w-4" />
    case 'planner':
      return <Lightbulb className="h-4 w-4" />
    case 'system':
      return <Bot className="h-4 w-4" />
    default:
      return <User className="h-4 w-4" />
  }
}

const ChatMessage = ({ message }: { message: any }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeDataset, setActiveDataset] = useState<any>(null);
  const isUser = message.type === 'user'
  const { activeProjectId, setActiveProject } = useProjects()
  const { tokens } = useAuthStore()

  useEffect(() => {
    const fetchProject = async () => {
      if (!activeProjectId) return;
      
      try {
        const response = await fetch(
          `${import.meta.env.VITE_BASE_API_URL}projects/${activeProjectId}`,
          {
            headers: {
              'Authorization': `Bearer ${tokens?.access_token}`
            }
          }
        );
        if (response.ok) {
          const data = await response.json();
          if (data.dataset) {
            setActiveDataset(data.dataset);
          }
        }
      } catch (error) {
        console.error('Error fetching project:', error);
      }
    };

    fetchProject();
  }, [activeProjectId]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !activeProjectId) return

    setIsUploading(true)
    setUploadProgress(0)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const xhr = new XMLHttpRequest();
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      };

      const uploadPromise = new Promise((resolve, reject) => {
        xhr.onload = () => resolve(xhr.response);
        xhr.onerror = () => reject(xhr.statusText);
        xhr.open('POST', `${import.meta.env.VITE_BASE_API_URL}projects/${activeProjectId}/dataset`);
        xhr.setRequestHeader('Authorization', `Bearer ${tokens?.access_token}`);
        xhr.responseType = 'json';
        xhr.send(formData);
      });

      const response = await uploadPromise as any;
      if (!response || response.error) {
        throw new Error(response?.error || 'Upload failed');
      }

      // Update active project with new data
      setActiveProject(response.project);
      setActiveDataset(response.dataset);

      // Send messages through WebSocket
      const ws = new WebSocket(
        `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${
          window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
        }/api/workflow/${activeProjectId}/ws?token=${encodeURIComponent(tokens?.access_token || '')}`
      );

      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'system',
          messageType: 'analyzer',
          messages: [
            {
              type: 'analyzer',
              content: `Dataset "${file.name}" uploaded successfully!`,
              dataset: response.dataset
            },
            {
              type: 'analyzer',
              content: `Great! I've analyzed your dataset. It contains:
                • ${response.dataset.statistics.rows} rows
                • ${response.dataset.statistics.columns} columns
                • Columns: ${response.dataset.statistics.column_names.join(', ')}`
            },
            {
              type: 'analyzer',
              content: "What would you like to know about your dataset?",
              dataset: response.dataset
            }
          ]
        }));
        ws.close();
      };

    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }

  const getStatisticsDisplay = (dataset: any) => {
    if (!dataset || !dataset.statistics) return null;
    const stats = dataset.statistics;
    return (
      <span className="text-xs text-muted-foreground">
        ({stats.rows} rows, {stats.columns} columns)
      </span>
    );
  };

  const getDatasetName = (messageDataset: any, activeDs: any) => {
    if (messageDataset?.name) return messageDataset.name;
    if (activeDs?.name) return activeDs.name;
    return "";
  };

  const handleWebSocket = (data: any, file: File) => {
    if (!activeProjectId || !tokens?.access_token) return;

    const ws = new WebSocket(
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${
        window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host
      }/api/workflow/${activeProjectId}/ws?token=${encodeURIComponent(tokens.access_token)}`
    );

    ws.onopen = () => {
      const initialMessages = [
        {
          type: 'analyzer',
          content: `Dataset "${file.name}" uploaded successfully!`,
          dataset: {
            name: file.name,
            path: data.dataset.path,
            statistics: data.dataset.statistics
          }
        },
        {
          type: 'analyzer',
          content: data.dataset.statistics ? 
            `Great! I've analyzed your dataset. It contains:
              • ${data.dataset.statistics.rows} rows
              • ${data.dataset.statistics.columns} columns
              • Columns: ${data.dataset.statistics.column_names.join(', ')}` :
            'Great! Your dataset has been uploaded.',
        },
        {
          type: 'analyzer',
          content: "What would you like to know about your dataset?",
          dataset: {
            name: file.name,
            path: data.dataset.path,
            statistics: data.dataset.statistics
          }
        }
      ];

      ws.send(JSON.stringify({
        type: 'system',
        messageType: 'analyzer',
        messages: initialMessages
      }));
      ws.close();
    };
  };

  const shouldShowUploadButton = (messageDataset: any, activeDs: any) => {
    if (!messageDataset) return false;
    if (activeDs?.path) return false;
    if (messageDataset.path) return false;
    return true;
  };

  return (
    <div
      className={cn(
        'mb-4 flex items-start gap-3',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      <Avatar className="h-8 w-8">
        <AvatarFallback className={cn(
          isUser ? 'bg-primary' : 'bg-muted',
          isUser ? 'text-primary-foreground' : 'text-muted-foreground'
        )}>
          <AgentIcon type={message.type} />
        </AvatarFallback>
      </Avatar>
      <div
        className={cn(
          'rounded-lg px-4 py-2 max-w-[80%]',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground',
          'shadow-sm'
        )}>
        {message.content}
        {message.dataset !== undefined && (
          <div className="mt-2">
            {(message.dataset?.path || (activeDataset?.path && message.type === 'analyzer')) ? (
              <div className="text-sm font-medium flex items-center gap-2 bg-muted/50 p-2 rounded">
                <Upload className="h-4 w-4" />
                <span>{getDatasetName(message.dataset, activeDataset)}</span>
                {getStatisticsDisplay(message.dataset || activeDataset)}
              </div>
            ) : (
              shouldShowUploadButton(message.dataset, activeDataset) && (
                <div className="flex flex-col gap-2">
                  <Input
                    type="file"
                    accept=".csv"
                    className="hidden"
                    id="csv-upload"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                  />
                  <label
                    htmlFor="csv-upload"
                    className={cn(
                      "flex items-center gap-2 px-3 py-1 text-sm text-background bg-primary rounded-md cursor-pointer hover:bg-primary/80 transition-colors p-2",
                      isUploading && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {isUploading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4" />
                    )}
                    {isUploading ? 'Uploading...' : 'Upload CSV'}
                  </label>
                  {isUploading && (
                    <Progress value={uploadProgress} className="h-1" />
                  )}
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  )
}

const ChatSection = () => {
  const { messages, isLoading } = useChat()
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <ScrollArea className="flex h-full flex-col bg-background" ref={scrollRef}>
      <div className="flex-1 p-4">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
      </div>
    </ScrollArea>
  )
}

export default ChatSection
