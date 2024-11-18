"use client";

import * as React from "react";
import { GalleryVerticalEnd } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { usePdfPlanStore } from "@/store/PdfPlanStore";
import { Rectangle } from "@/models/pdf_plan";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const boundingBoxes = usePdfPlanStore((state) => state.boundingBoxes);
  const selectedRectId = usePdfPlanStore((state) => state.selectedRectId);
  const setSelectedRectId = usePdfPlanStore((state) => state.setSelectedRectId);
  const currentRect = usePdfPlanStore((state) => state.currentRect);
  const setCurrentRect = usePdfPlanStore((state) => state.setCurrentRect);

  // Ref to store references to each sidebar item
  const itemRefs = React.useRef<{ [key: number]: HTMLAnchorElement | null }>({});

  const handleRectClick = (boxId: number) => {
    const selectedRect = boundingBoxes.find((box: Rectangle) => box.id === boxId);
    setCurrentRect(selectedRect);
    setSelectedRectId(boxId);
  };

  React.useEffect(() => {
    if (selectedRectId != null && itemRefs.current[selectedRectId]) {

      // Small timeout to ensure the element is rendered before scrolling
      setTimeout(() => {
        itemRefs.current[selectedRectId]?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "start",
        });
      }, 100);
    }
  }, [selectedRectId]);

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
                    <span className="font-semibold">Symbols</span>
                  </div>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu>
            {boundingBoxes.map((box: Rectangle) => {
              const isSelected = box.id === selectedRectId;
              return (
                <SidebarMenuButton key={box.id} asChild>
                  <a
                    href="#"
                    onClick={() => handleRectClick(box.id)}
                    ref={(el) => {
                      itemRefs.current[box.id] = el;
                    }}
                    className={`block p-2 rounded-md ${
                      isSelected
                        ? "bg-blue-500 text-white border-l-4 border-blue-700"
                        : "hover:bg-gray-100 border-l-4 border-transparent"
                    }`}
                  >
                    <span style={{ color: isSelected ? "inherit" : box.color }}>
                      {box.name}
                    </span>
                  </a>
                </SidebarMenuButton>
              );
            })}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
