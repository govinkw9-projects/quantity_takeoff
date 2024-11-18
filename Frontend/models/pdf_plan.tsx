

export interface pdfFile {
    id: number;
    fileName: string;
    fileurl: string;
  }


export  type Handle = 'nw' | 'ne' | 'sw' | 'se' | 'n' | 's' | 'w' | 'e';

  
export  interface RectangleHandles {
    nw: Handle;
    ne: Handle;
    sw: Handle;
    se: Handle;
    n: Handle;
    s: Handle;
    w: Handle;
    e: Handle;
    null: Handle;
  }
  
export   interface Rectangle {
    name: string, 
    id: number; 
    x: number;
    y: number;
    width: number;
    height: number;
    color: string;
  }
  