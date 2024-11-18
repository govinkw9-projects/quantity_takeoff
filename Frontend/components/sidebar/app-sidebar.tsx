"use client";

import * as React from "react";
import { GalleryVerticalEnd, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";

import { Button } from "@/components/ui/button";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import { usePdfPlanStore } from "@/store/PdfPlanStore";
import { Rectangle } from "@/models/pdf_plan";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const boundingBoxes = usePdfPlanStore((state) => state.boundingBoxes);
  const selectedRectId = usePdfPlanStore((state) => state.selectedRectId);
  const setSelectedRectId = usePdfPlanStore((state) => state.setSelectedRectId);
  const currentRect = usePdfPlanStore((state) => state.currentRect);
  const setCurrentRect = usePdfPlanStore((state) => state.setCurrentRect);
  const updateBoundingBoxName = usePdfPlanStore((state) => state.updateBoundingBoxName);
  const removeBoundingBox = usePdfPlanStore((state) => state.removeBoundingBox);

  const { isMobile } = useSidebar();

  const itemRefs = React.useRef<{ [key: number]: HTMLDivElement | null }>({});

  const [renamingBoxId, setRenamingBoxId] = React.useState<number | null>(null);
  const [newBoxName, setNewBoxName] = React.useState<string>("");
  const [deleteBoxId, setDeleteBoxId] = React.useState<number | null>(null);

  const handleRectClick = (boxId: number) => {
    const selectedRect = boundingBoxes.find((box: Rectangle) => box.id === boxId);
    setCurrentRect(selectedRect);
    setSelectedRectId(boxId);
  };

  React.useEffect(() => {
    if (selectedRectId != null && itemRefs.current[selectedRectId]) {
      setTimeout(() => {
        itemRefs.current[selectedRectId]?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "start",
        });
      }, 100);
    }
  }, [selectedRectId]);

  const handleRename = (boxId: number) => {
    const box = boundingBoxes.find((box: Rectangle) => box.id === boxId);
    setRenamingBoxId(boxId);
    setNewBoxName(box?.name || "");
  };

  const saveNewName = (boxId: number) => {
    if (newBoxName.trim() !== "") {
      updateBoundingBoxName(boxId, newBoxName.trim());
    }
    setRenamingBoxId(null);
  };

  const handleDelete = (boxId: number) => {
    setDeleteBoxId(boxId);
  };

  const confirmDelete = () => {
    if (deleteBoxId != null) {
      removeBoundingBox(deleteBoxId);
      if (selectedRectId === deleteBoxId) {
        setSelectedRectId(null);
        setCurrentRect(null);
      }
      setDeleteBoxId(null);
    }
  };

  const cancelDelete = () => {
    setDeleteBoxId(null);
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
                  <div className="relative flex items-center justify-between p-2 rounded-md cursor-pointer hover:bg-gray-100 mb-2">
                    <div
                      onClick={() => handleRectClick(box.id)}
                      ref={(el) => {
                        itemRefs.current[box.id] = el;
                      }}
                      className={`flex-1 ${
                        isSelected
                          ? "bg-blue-500 text-white border-l-4 border-blue-700"
                          : "border-l-4 border-transparent"
                      }`}
                    >
                      {box.id === renamingBoxId ? (
                        <input
                          type="text"
                          value={newBoxName}
                          onChange={(e) => setNewBoxName(e.target.value)}
                          onBlur={() => saveNewName(box.id)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              saveNewName(box.id);
                            } else if (e.key === "Escape") {
                              setRenamingBoxId(null);
                            }
                          }}
                          autoFocus
                          className="w-full px-2 py-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                        />
                      ) : (
                        <span
                          style={{ color: isSelected ? "inherit" : box.color }}
                          title={box.name}
                          className="text-clip overflow-hidden white-space: nowrap;"
                        >
                          {box.name}
                        </span>
                      )}
                    </div>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0 flex-shrink-0">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent
                        className="w-56 rounded-lg"
                        side={isMobile ? "bottom" : "right"}
                        align={isMobile ? "end" : "start"}
                      >
                        <DropdownMenuItem onClick={() => handleRename(box.id)}>
                          <Pencil className="mr-2 h-4 w-4" />
                          <span>Rename</span>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleDelete(box.id)}>
                          <Trash2 className="mr-2 h-4 w-4" />
                          <span>Delete</span>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </SidebarMenuButton>
              );
            })}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />

      {deleteBoxId != null && (
        <AlertDialog open={deleteBoxId != null} onOpenChange={cancelDelete}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Delete</AlertDialogTitle>
            </AlertDialogHeader>
            <div className="py-4">
              Are you sure you want to delete symbol: "
              {boundingBoxes.find((box:Rectangle) => box.id === deleteBoxId)?.name}"?
            </div>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={cancelDelete}>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={confirmDelete}>Delete</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </Sidebar>
  );
}
