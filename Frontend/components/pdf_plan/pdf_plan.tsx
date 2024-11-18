"use client"

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { Button } from "@/components/ui/button"

import { usePdfPlanStore } from '@/store/PdfPlanStore';
import { SubmitPopup } from "@/components/pdf_plan/submit"; 
import { Configuration } from "@/lib/config"

import { Rectangle, RectangleHandles, Handle } from '@/models/pdf_plan';
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.js`;

export function PdfViewer() {
  const pdfCanvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null); // Ref to the scrollable container
  const [pdfDocument, setPdfDocument] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const pdfUrl = usePdfPlanStore((state) => state.pdfUrl);
  const [scale, setScale] = useState(Configuration.pdfJsScaleFactor);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isMoving, setIsMoving] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [resizeHandle, setResizeHandle] = useState<Handle | null>(null);
  const renderTaskRef = useRef<pdfjsLib.PDFRenderTask | null>(null);

  const [contextMenuVisible, setContextMenuVisible] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const [contextMenuRectId, setContextMenuRectId] = useState<number | null>(null);
  const [defaultName, setdefaultName] = useState("")

  const [isDialogOpen, setDialogOpen] = useState(false)

  const colorMapRef = useRef<{ [name: string]: string }>({});


  // Store 
  const selectedRectId = usePdfPlanStore((state) => state.selectedRectId);
  const setSelectedRectId = usePdfPlanStore((state) => state.setSelectedRectId);
  const boundingBoxes = usePdfPlanStore((state) => state.boundingBoxes);
  const addBoundingBox = usePdfPlanStore((state) => state.addBoundingBox);
  const updateBoundingBox = usePdfPlanStore((state) => state.updateBoundingBox);
  const removeBoundingBox = usePdfPlanStore((state) => state.removeBoundingBox);
  const currentRect = usePdfPlanStore((state) => state.currentRect);
  const setCurrentRect = usePdfPlanStore((state) => state.setCurrentRect);

  useEffect(() => {
    if (pdfUrl) {
      const loadingTask = pdfjsLib.getDocument(pdfUrl);
      loadingTask.promise.then(
        (pdfDoc) => {
          setPdfDocument(pdfDoc);
        },
        (reason) => {
          console.error('Error loading PDF:', reason);
        }
      );
    }
  }, [pdfUrl]);

  useEffect(() => {
    if (pdfDocument) {
      renderPage();
    }
  }, [pdfDocument, scale]);

  useEffect(() => {
      drawRectangles();
  }, [currentRect, selectedRectId, boundingBoxes]);

  const renderPage = async () => {
    if(pdfDocument){
      const page = await pdfDocument.getPage(1); // Render the first page
      const viewport = page.getViewport({ scale });
      const pdfCanvas = pdfCanvasRef.current;
      const overlayCanvas = overlayCanvasRef.current;
      let context = null ; 
      
      if(pdfCanvas && overlayCanvas){
        pdfCanvas.width = viewport.width;
        pdfCanvas.height = viewport.height;
        overlayCanvas.width = viewport.width;
        overlayCanvas.height = viewport.height;
        context = pdfCanvas.getContext('2d');

      } 

      // Cancel any previous render task
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
      }
  
      // Render PDF page into canvas context
      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };
      const renderTask = page.render(renderContext);
      renderTaskRef.current = renderTask;
  
      try {
        await renderTask.promise;
        renderTaskRef.current = null;
  
        // Draw existing rectangles after rendering the page
        drawRectangles();
      } catch (error) {
        if (error instanceof pdfjsLib.RenderingCancelledException) {
          // Rendering was cancelled, no action needed
        } else {
          console.error('Render error:', error);
        }
      }
    }
 
  };

  const getMousePos = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = overlayCanvasRef.current.getBoundingClientRect();
    const x = (event.clientX - rect.left) * (overlayCanvasRef.current.width / rect.width);
    const y = (event.clientY - rect.top) * (overlayCanvasRef.current.height / rect.height);
    return { x, y };
  };

  const handleMouseDown = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y } = getMousePos(event);

    // Check if clicking on a resize handle
    const handle = getHandleUnderMouse(x, y);
    if (handle && selectedRectId !== null) {
      setIsResizing(true);
      setResizeHandle(handle);
      setStartPoint({ x, y });
      return;
    }

    // Check if clicking inside a bounding box
    const rectUnderMouse = getBoundingBoxUnderMouse(x, y);
    if (rectUnderMouse) {
      setSelectedRectId(rectUnderMouse.id);
      setIsMoving(true);
      setStartPoint({ x, y });
      return;
    }

    // Start drawing a new rectangle
    setSelectedRectId(null);
    setStartPoint({ x, y });
    setIsDrawing(true);
  };

  const handleMouseUp = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDrawing && currentRect) {
      setDialogOpen(true) 
      setIsDrawing(false)
    } else if (isMoving) {
      setIsMoving(false)
    } else if (isResizing) {
      setIsResizing(false)
      setResizeHandle(null)
    }
  }
  
  const handleDialogCancel = () => {
    setCurrentRect(null); // Clear currentRect
    setDialogOpen(false); // Close the dialog
  };

  const handleDialogSubmit = (name: string) => {
    if (currentRect) {
      let color = '';
      if (colorMapRef.current[name]) {
        color = colorMapRef.current[name];
      } else {
        // Generate a new color for the new name
        color = getColorForName(name);
        colorMapRef.current[name] = color;
      }

      const newRect: Rectangle = {
        ...currentRect,
        id: Date.now(),
        name,
        color,
      };

      // Update colors of other rectangles with the same name
      boundingBoxes.forEach((rect) => {
        if (rect.name === name) {
          rect.color = color;
          updateBoundingBox(rect.id, rect); // Update the rectangle in the store
        }
      });

      addBoundingBox(newRect); // Add to the store
    }
    setDialogOpen(false); // Close the dialog
    setCurrentRect(null);
    setSelectedRectId(null); 
    setdefaultName(name) ; 
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Delete' && selectedRectId !== null) {
      deleteSelectedRectangle();
    }
  };
  
  const deleteSelectedRectangle = () => {
    removeBoundingBox(selectedRectId);
    setSelectedRectId(null);
    drawRectangles();
  };

  const getBoundingBoxUnderMouse = (x: number, y: number) => {
    return boundingBoxes
      .slice()
      .reverse()
      .find((rect) => x >= rect.x && x <= rect.x + rect.width && y >= rect.y && y <= rect.y + rect.height);
  };

  const getHandleUnderMouse = (x: number, y: number) => {
    if (selectedRectId === null) return null;
    const rect = boundingBoxes.find((box:Rectangle) => box.id === selectedRectId);
    if (!rect) return null;

    const handles = getHandles(rect);
    for (const [position, handleRect] of Object.entries(handles)) {
      if (
        x >= handleRect.x &&
        x <= handleRect.x + handleRect.width &&
        y >= handleRect.y &&
        y <= handleRect.y + handleRect.height
      ) {
        return position as Handle;
      }
    }
    return null;
  };

  const getHandles = (rect:Rectangle) => {
    const size = 8;
    return {
      nw: { x: rect.x - size / 2, y: rect.y - size / 2, width: size, height: size },
      ne: { x: rect.x + rect.width - size / 2, y: rect.y - size / 2, width: size, height: size },
      sw: { x: rect.x - size / 2, y: rect.y + rect.height - size / 2, width: size, height: size },
      se: { x: rect.x + rect.width - size / 2, y: rect.y + rect.height - size / 2, width: size, height: size },
      n: { x: rect.x + rect.width / 2 - size / 2, y: rect.y - size / 2, width: size, height: size },
      s: { x: rect.x + rect.width / 2 - size / 2, y: rect.y + rect.height - size / 2, width: size, height: size },
      w: { x: rect.x - size / 2, y: rect.y + rect.height / 2 - size / 2, width: size, height: size },
      e: { x: rect.x + rect.width - size / 2, y: rect.y + rect.height / 2 - size / 2, width: size, height: size },
    };
  };

  const getCursorForHandle = (handle:Handle) => {
    const cursors = {
      nw: 'nwse-resize',
      se: 'nwse-resize',
      ne: 'nesw-resize',
      sw: 'nesw-resize',
      n: 'ns-resize',
      s: 'ns-resize',
      w: 'ew-resize',
      e: 'ew-resize',
    };
    return cursors[handle] || 'default';
  };

  const resizeBoundingBox = (rect:Rectangle, x:number, y:number, handle:Handle) => {
    let { x: rectX, y: rectY, width, height } = rect;
    const minSize = 10;

    switch (handle) {
      case 'nw':
        width += rectX - x;
        height += rectY - y;
        rectX = x;
        rectY = y;
        break;
      case 'ne':
        width = x - rectX;
        height += rectY - y;
        rectY = y;
        break;
      case 'sw':
        width += rectX - x;
        height = y - rectY;
        rectX = x;
        break;
      case 'se':
        width = x - rectX;
        height = y - rectY;
        break;
      case 'n':
        height += rectY - y;
        rectY = y;
        break;
      case 's':
        height = y - rectY;
        break;
      case 'w':
        width += rectX - x;
        rectX = x;
        break;
      case 'e':
        width = x - rectX;
        break;
      default:
        break;
    }

    // Enforce minimum size
    width = Math.max(width, minSize);
    height = Math.max(height, minSize);

    return { ...rect, x: rectX, y: rectY, width, height };
  };

  const handleMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y } = getMousePos(event);

    if (isDrawing && startPoint) {
      const width = x - startPoint.x;
      const height = y - startPoint.y;

      setCurrentRect({
        x: startPoint.x,
        y: startPoint.y,
        width: width,
        height: height,
      });

      drawRectangles();
    } else if (isMoving && startPoint && selectedRectId !== null) {
      const dx = x - startPoint.x;
      const dy = y - startPoint.y;
      const rect = boundingBoxes.find((box:Rectangle) => box.id === selectedRectId);
      if (rect) {
        const updatedRect = { ...rect, x: rect.x + dx, y: rect.y + dy };
        updateBoundingBox(selectedRectId, updatedRect);
        setStartPoint({ x, y });
        drawRectangles();
      }
    } else if (isResizing && startPoint && selectedRectId !== null && resizeHandle) {
      const rect = boundingBoxes.find((box:Rectangle) => box.id === selectedRectId);
      if (rect) {
        const updatedRect = resizeBoundingBox(rect, x, y, resizeHandle);
        updateBoundingBox(selectedRectId, updatedRect);
        setStartPoint({ x, y });
        drawRectangles();
      }
    } else {
      // Change cursor based on what is under the mouse
      const handle = getHandleUnderMouse(x, y);
      if (handle) {
        overlayCanvasRef.current!.style.cursor = getCursorForHandle(handle);
      } else if (getBoundingBoxUnderMouse(x, y)) {
        overlayCanvasRef.current!.style.cursor = 'move';
      } else {
        overlayCanvasRef.current!.style.cursor = 'crosshair';
      }
    }
  };

const getColorForName = (name: string) => {
  if (colorMapRef.current[name]) {
    return colorMapRef.current[name];
  } else {
    const normalized = name.trim().toLowerCase();
    let hash = 0;
    for (let i = 0; i < normalized.length; i++) {
      hash = normalized.charCodeAt(i) + ((hash << 5) - hash);
    }
    const h = Math.abs(hash % 360);
    const color = `hsl(${h}, 70%, 50%)`;
    colorMapRef.current[name] = color;
    return color;
  }
};

  const drawRectangles = () => {
    const overlayCanvas = overlayCanvasRef.current;
    const context = overlayCanvas?.getContext('2d');
    if (!context) return;

    // Clear existing drawings
    context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    // Draw existing rectangles from the store
    boundingBoxes.forEach((rect: Rectangle) => {
      const color = rect.color;

      // If the rectangle is selected, apply different styling
      if (rect.id === selectedRectId) {
        context.strokeStyle = 'yellow';
        context.lineWidth = 3;
      } else {
        context.strokeStyle = color;
        context.lineWidth = 3;
      }

      context.strokeRect(rect.x, rect.y, rect.width, rect.height);

      if (rect.id === selectedRectId) {
        // Draw selection highlight
        context.strokeStyle = 'blue';
        context.lineWidth = 4;
        context.strokeRect(rect.x, rect.y, rect.width, rect.height);

        // Draw resize handles
        const handles = getHandles(rect);
        context.fillStyle = 'white';
        context.strokeStyle = 'black';
        Object.values(handles).forEach((handleRect) => {
          context.fillRect(handleRect.x, handleRect.y, handleRect.width, handleRect.height);
          context.strokeRect(handleRect.x, handleRect.y, handleRect.width, handleRect.height);
        });
      }

    });
    
    if (currentRect && !selectedRectId) {
      context.strokeStyle = 'red';
      context.lineWidth = 3;
      context.strokeRect(
        currentRect.x,
        currentRect.y,
        currentRect.width,
        currentRect.height
      );
    }
  };

  const handleContextMenu = (event: React.MouseEvent<HTMLCanvasElement>) => {
      event.preventDefault();
      const { x, y } = getMousePos(event);

      const rectUnderMouse = getBoundingBoxUnderMouse(x, y);
      if (rectUnderMouse) {
        setSelectedRectId(rectUnderMouse.id);
        setContextMenuRectId(rectUnderMouse.id);
        setContextMenuPosition({ x: event.clientX, y: event.clientY });
        setContextMenuVisible(true);
        drawRectangles();
      } else {
        setContextMenuVisible(false);
      }
    };


  const handleDeleteRectangle = () => {
    if (selectedRectId !== null) {
      removeBoundingBox(selectedRectId);
      setSelectedRectId(null);
      drawRectangles();
      setCurrentRect(null);
    }
  };

  const selectedRect = boundingBoxes.find((box: Rectangle) => box.id === selectedRectId);

  // Calculate adjusted positions
  let adjustedLeft = 0;
  let adjustedTop = 0;

  if (selectedRect && overlayCanvasRef.current) {
    const canvasRect = overlayCanvasRef.current.getBoundingClientRect();
    const scaleX = overlayCanvasRef.current.width / canvasRect.width;
    const scaleY = overlayCanvasRef.current.height / canvasRect.height;

    adjustedLeft = (selectedRect.x + selectedRect.width / 2) / scaleX  ;
    adjustedTop = (selectedRect.y + selectedRect.height / 2) / scaleY ;
  }

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (contextMenuVisible) {
        setContextMenuVisible(false);
      }
    };

    window.addEventListener('click', handleClickOutside);
    return () => {
      window.removeEventListener('click', handleClickOutside);
    };
  }, [contextMenuVisible]);

  useEffect(() => {
    if (selectedRectId == null || !scrollContainerRef.current || !overlayCanvasRef.current) return;
  
    const selectedRect = boundingBoxes.find((box: Rectangle) => box.id === selectedRectId);
    if (!selectedRect) return;
  
    const container = scrollContainerRef.current;
    const canvas = overlayCanvasRef.current;
  
    // Get the rectangle's position relative to the viewport
    const rectLeft = selectedRect.x - container.scrollLeft;
    const rectTop = selectedRect.y - container.scrollTop;
    const rectRight = rectLeft + selectedRect.width;
    const rectBottom = rectTop + selectedRect.height;
  
    setdefaultName(selectedRect.name)

    // Check if the rectangle is fully within the view
    const isFullyInView =
      rectLeft >= 0 &&
      rectTop >= 0 &&
      rectRight <= container.clientWidth &&
      rectBottom <= container.clientHeight;
  
    if (isFullyInView) return; // Don't scroll if the rectangle is already fully in view
  
    // Calculate the center of the rectangle
    const rectCenterX = selectedRect.x + selectedRect.width / 2;
    const rectCenterY = selectedRect.y + selectedRect.height / 2;
  
    // Calculate the desired scroll positions to center the rectangle
    const desiredScrollLeft = rectCenterX - container.clientWidth / 2;
    const desiredScrollTop = rectCenterY - container.clientHeight / 2;
  
    // Clamp the scroll positions to prevent overflow
    const maxScrollLeft = canvas.width - container.clientWidth;
    const maxScrollTop = canvas.height - container.clientHeight;
  
    const scrollLeft = Math.max(0, Math.min(desiredScrollLeft, maxScrollLeft));
    const scrollTop = Math.max(0, Math.min(desiredScrollTop, maxScrollTop));
  
    // Perform the scroll
    container.scrollTo({
      top: scrollTop,
      left: scrollLeft,
      behavior: "smooth",
    });
  }, [selectedRectId, boundingBoxes]);
  
  
  return (
    <div
      onKeyDown={handleKeyDown}
      tabIndex={0} // Make div focusable for keyboard events
      className="flex flex-col h-[90vh]w-full overflow-hidden" // Hide outer scrollbar with overflow-hidden
    >
      <h1 className="text-xl font-bold text-center mb-4">Analysis</h1>
  
      <SubmitPopup
        onSubmit={handleDialogSubmit}
        onCancel={handleDialogCancel}
        isOpen={isDialogOpen}
        closeDialog={() => setDialogOpen(false)}
        defaultName={defaultName}
      />
  
      <div
        ref={scrollContainerRef}
        style={{
          width: '100%',
          height: '100%',
          overflow: 'auto', // Enable scrolling only on this div
          border: '1px solid #ccc',
          position: 'absolute', // Relative positioning for absolute children
        }}
        className="flex-1"
      >
        <canvas ref={pdfCanvasRef} style={{ border: '1px solid black' }} />
        <canvas
          ref={overlayCanvasRef}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            cursor: 'crosshair',
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onContextMenu={handleContextMenu} // Add context menu handler
        />
  
        {contextMenuVisible && selectedRect && (
          <div
            style={{
              position: 'absolute',
              top: adjustedTop + 90,
              left: adjustedLeft + 90,
              zIndex: 1000,
              background: 'white',
              border: '1px solid #ccc',
              padding: '8px',
              borderRadius: '4px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
            }}
          >
            <Button type="button" onClick={handleDeleteRectangle}>
              Delete
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}  