import * as React from "react";
import { Command, File, Inbox, MessageCircle, Plus } from "lucide-react";

import { Label } from "@/components/ui/label";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Switch } from "@/components/ui/switch";
import { NavUser } from "../navbar/nav-user";
import { dummyProjects } from "@/lib/dummyData";

import useProjects from "@/hooks/useProjects";
import { formatDate } from "@/utils/formater";
import useAuthStore from "@/hooks/useAuthStore";
import { LoginCard } from "../cards/login-card";

const data = {
  user: {
    name: "shadcn",
    email: "m@example.com",
    avatar: "/avatars/shadcn.jpg",
  },

  navMain: [
    {
      title: "Chats",
      url: "#",
      icon: MessageCircle,
      isActive: true,
    },
    {
      title: "Reports",
      url: "#",
      icon: File,
      isActive: false,
    },
  ],

  mails: [
    {
      name: "William Smith",
      email: "williamsmith@example.com",
      subject: "Meeting Tomorrow",
      date: "09:34 AM",
      teaser:
        "Hi team, just a reminder about our meeting tomorrow at 10 AM.\nPlease come prepared with your project updates.",
    },
    {
      name: "Alice Smith",
      email: "alicesmith@example.com",
      subject: "Re: Project Update",
      date: "Yesterday",
      teaser:
        "Thanks for the update. The progress looks great so far.\nLet's schedule a call to discuss the next steps.",
    },
  ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const [activeItem, setActiveItem] = React.useState(data.navMain[0]);
  const [mails, setMails] = React.useState(data.mails);
  const { setOpen } = useSidebar();
  const { projects, activeProjectId, setActiveProject } = useProjects();
  const { isAuthenticated, user } = useAuthStore();

  React.useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash.startsWith("#proj_")) {
        setActiveProject(hash.replace("#proj_", ""));
      } else {
        setActiveProject(null);
      }
    };

    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, [setActiveProject]);

  console.log(activeProjectId);

  return (
    <Sidebar
      collapsible="icon"
      className="overflow-hidden [&>[data-sidebar=sidebar]]:flex-row"
      {...props}
    >
      <Sidebar
        collapsible="none"
        className="!w-[calc(var(--sidebar-width-icon)_+_4px)] border-r"
      >
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg" asChild className="md:h-8 md:p-0">
                <a href="#">
                  <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                    <Command className="size-4" />
                  </div>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">Data Buddy</span>
                  </div>
                </a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupContent className="px-1.5 md:px-0">
              <SidebarMenu>
                {data.navMain.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      tooltip={{
                        children: item.title,
                        hidden: false,
                      }}
                      // onClick={() => {
                      //   setActiveItem(item);
                      //   const mail = data.mails.sort(() => Math.random() - 0.5);
                      //   setMails(
                      //     mail.slice(
                      //       0,
                      //       Math.max(5, Math.floor(Math.random() * 10) + 1)
                      //     )
                      //   );
                      //   setOpen(true);
                      // }}
                      isActive={activeItem.title === item.title}
                      className="px-2.5 md:px-2"
                    >
                      <item.icon />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
          {isAuthenticated && user && <NavUser user={user} />}
        </SidebarFooter>
      </Sidebar>

      <Sidebar collapsible="none" className="hidden flex-1 md:flex">
        <SidebarHeader className="gap-3.5 border-b p-4">
          <div className="flex w-full items-center justify-between">
            <div className="text-base font-medium text-foreground">
              {activeItem.title}
            </div>
            <Label className="flex items-center gap-2 text-sm">
              <span>Active</span>
              <Switch className="shadow-none" />
            </Label>
          </div>
        </SidebarHeader>
        <SidebarContent className="flex flex-col flex-grow">
          <SidebarMenu className="px-0">
            <SidebarMenuItem className="mt-3 mx-2">
              <SidebarMenuButton
                type="button"
                className="flex items-center justify-center"
                variant="outline"
              >
                <Plus />
                <span className="text-sm">Add New Project</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>

          {isAuthenticated ? (
            <SidebarGroup className="px-0 flex-grow">
              <SidebarGroupContent>
                {projects.map((project) => (
                  <a
                    href={`#proj_${project.id}`}
                    key={project.id}
                    className={`flex flex-col items-start gap-1 p-4 text-sm leading-tight hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:m-1 hover:rounded-md ${
                      project.id === activeProjectId
                        ? "bg-sidebar-accent text-sidebar-accent-foreground m-1 rounded-md"
                        : "border-b last:border-b-0"
                    }`}
                  >
                    <div className="flex w-full items-center gap-2">
                      <span className="font-semibold">{project.name}</span>{" "}
                      <span className="ml-auto text-xs">
                        {formatDate(project.created_at)}
                      </span>
                    </div>
                    <span className="line-clamp-2 w-full whitespace-break-spaces text-xs">
                      {project?.description}
                    </span>
                  </a>
                ))}
              </SidebarGroupContent>
            </SidebarGroup>
          ) : (
            <div className="flex-grow flex items-end p-4">
              <LoginCard />
            </div>
          )}
        </SidebarContent>
      </Sidebar>
    </Sidebar>
  );
}
