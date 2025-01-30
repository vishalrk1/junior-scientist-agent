import * as React from "react";
import { Command } from "lucide-react";
import { NavUser } from "../navbar/nav-user";
import { useLocation, useNavigate } from "react-router-dom";
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
} from "@/components/ui/sidebar";
import { User } from "@/lib/types";
import { ModeToggle } from "../toogle-theme";
import useNavStore from "@/store/useNavStore";

interface IconSidebarProps {
  navItems: Array<{
    title: string;
    icon: React.ElementType;
    isActive: boolean;
    url: string;
  }>;
  user?: User | null;
  isAuthenticated: boolean;
}

export function IconSidebar({ navItems, user, isAuthenticated }: IconSidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { setActiveItem, activeItem } = useNavStore();

  const handleNavigation = (item: typeof navItems[number]) => {
    navigate(item.url);
    setActiveItem(item.url);
  };

  React.useEffect(() => {
    setActiveItem(location.pathname);
  }, [location.pathname, setActiveItem]);

  return (
    <Sidebar collapsible="none" className="!w-[calc(var(--sidebar-width-icon)_+_4px)] border-r">
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
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    tooltip={{
                      children: item.title,
                      hidden: false,
                    }}
                    isActive={activeItem.title === item.title}
                    className="px-2.5 md:px-2"
                    onClick={() => handleNavigation(item)}
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
        <ModeToggle />
        {isAuthenticated && user && <NavUser user={user} />}
      </SidebarFooter>
    </Sidebar>
  );
}
