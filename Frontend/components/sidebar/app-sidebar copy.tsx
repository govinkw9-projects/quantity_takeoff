"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { GalleryVerticalEnd, Minus, Plus } from "lucide-react";
import { useRouter } from "next/navigation"; // Using 'next/navigation' for 'App Router' compatibility

import { SearchForm } from "@/components/sidebar/search-form";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { ToastAction } from "@/components/ui/toast";
import { useAudioStore } from "@/store/useAudioStore";
import {AudioFile} from "@/models/audio_stream"

interface NavItem {
  title: string;
  url: string;
  isActive?: boolean;
}

interface InspectionDataItem {
  title: string;
  url: string;
  items: NavItem[];
}



export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  const setAudioFiles = useAudioStore((state) => state.setAudioFiles);
  const audioFiles = useAudioStore((state) => state.audioFiles);
  const router = useRouter();

  useEffect(() => {
    const fetchAudioFiles = async () => {
        try {
            const response = await fetch('/api/allAudio?data=fileName');
            const data = await response.json();
            setAudioFiles(data);
        } catch (error) {
            console.error('Error fetching audio files:', error);
        }
    };

    fetchAudioFiles();
}, []);


  const handleSync = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/syncaudio?days=1");
      if (!response.ok) {
        throw new Error("Failed to sync audio files");
      }
  
      const data = await response.json();

      toast({
        title: "Sync Successful",
        description: data.message,
        action: <ToastAction altText="Done">Done</ToastAction>,
      });
    } catch (error) {
      console.log(error)
      toast({
        variant: "destructive",
        title: "Sync Failed",
        description: "An error occurred while syncing audio files.",
      });
    } finally {
      setLoading(false);
    }
  };

  const inspectionData: { navMain: InspectionDataItem[] } = {
    navMain: audioFiles.map((audiofile: AudioFile) => ({
      title: audiofile.fileName.replace(/\.[^/.]+$/, ""),  
      url: `/audio/${audiofile.fileName}`,
      items: [
        { title: "Report", url: `/audio/${audiofile.fileName}` }
      ],
    })),
  };
  

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <a href="#">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <GalleryVerticalEnd className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">Reports</span>
                    <Button 
                      className="justify-center"
                      onClick={handleSync} 
                      disabled={loading}
                    >
                      {loading ? "Syncing..." : "Sync"}
                    </Button>
                  </div>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <SearchForm />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu>
            {inspectionData.navMain.map((item: InspectionDataItem, index: number) => (
              <Collapsible
                key={item.title}
                defaultOpen={index === 1}
                className="group/collapsible"
              >
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton 
                    onClick={() => handleNavigation(item.url)}
                    >
                      {item.title}{""}
                      <Plus className="ml-auto group-data-[state=open]/collapsible:hidden" />
                      <Minus className="ml-auto group-data-[state=closed]/collapsible:hidden" />
                      
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  {item.items?.length ? (
                    <CollapsibleContent>
                      <SidebarMenuSub>
                        {item.items.map((subItem: NavItem) => (
                          <SidebarMenuSubItem key={subItem.title}>
                            <SidebarMenuSubButton
                              asChild
                              isActive={subItem.isActive}
                              onClick={() => handleNavigation(subItem.url)}
                            >
                              <a>{subItem.title}</a>
                            </SidebarMenuSubButton>
                          </SidebarMenuSubItem>
                        ))}
                      </SidebarMenuSub>
                    </CollapsibleContent>
                  ) : null}
                </SidebarMenuItem>
              </Collapsible>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
