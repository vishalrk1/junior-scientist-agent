import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { ThemeProvider } from "@/contexts/theme-provider";
import { Settings, Star } from "lucide-react";

import React from "react";

const Dashboard = () => {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <SidebarProvider
        style={
          {
            "--sidebar-width": "350px",
          } as React.CSSProperties
        }
      >
        <AppSidebar />
        <SidebarInset>
          <header className="sticky top-0 flex shrink-0 items-center gap-2 border-b bg-background p-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbPage className="line-clamp-1">
                    Project Management & Task Tracking
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
            <div className="ml-auto px-3">
              <div className="flex items-center gap-2 text-sm">
                <div className="hidden font-medium text-muted-foreground md:inline-block">
                  Edit Oct 08
                </div>
                <Button variant="ghost" size="icon" className="h-7 w-7">
                  <Star />
                </Button>
                <Separator orientation="vertical" className="mr-2 h-4" />
                <Button variant="ghost" size="icon" className="h-7 w-7">
                  <Settings />
                </Button>
              </div>
            </div>
          </header>
          <div className="flex flex-1 flex-col gap-4 p-4"></div>
        </SidebarInset>
      </SidebarProvider>
    </ThemeProvider>
  );
};

export default Dashboard;
