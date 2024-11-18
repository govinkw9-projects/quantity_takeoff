import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const usePdfPlanStore = create(
  (set) => ({
    pdfName: null,
    pdfUrl: null,
    boundingBoxes: [], // Array of bounding box objects
    selectedName: null, // The currently selected name in the sidebar
    selectedRectId: null, // Add this if not already present
    currentRect: null, // Add currentRect to the store

    setPdfName: (pdfName) => set({ pdfName }),
    setPdfUrl: (pdfUrl) => set({ pdfUrl }),
    setLegendUrl: (legendUrl) => set({ legendUrl }),
    setLegendName: (legendName) => set({ legendName }),
    
    addBoundingBox: (boundingBox) =>
      set((state) => ({ boundingBoxes: [...state.boundingBoxes, boundingBox] })),
    updateBoundingBox: (boxId, updatedBox) =>
      set((state) => ({
        boundingBoxes: state.boundingBoxes.map((box) =>
          box.id === boxId ? { ...box, ...updatedBox } : box
        ),
      })),
    setBoundingBoxes: (boundingBoxes) => set({ boundingBoxes }),
    removeBoundingBox: (boxId) =>
      set((state) => ({
        boundingBoxes: state.boundingBoxes.filter((box) => box.id !== boxId),
      })),
    setSelectedRectId: (rectId) => set({ selectedRectId: rectId }),
    setCurrentRect: (rect) => set({ currentRect: rect }),  

    updateBoundingBoxName: (boxId, newName) =>
      set((state) => ({
        boundingBoxes: state.boundingBoxes.map((box) =>
          box.id === boxId ? { ...box, name: newName } : box
        ),
      })),
    removeBoundingBox: (boxId) =>
      set((state) => ({
        boundingBoxes: state.boundingBoxes.filter((box) => box.id !== boxId),
      })),


  }),
  {
    name: 'pdf-plan-store', // Name of the storage item
  }
);

// export const usePdfPlanStore = create(
//   persist(
//     (set) => ({
//       pdfName: null,
//       pdfUrl: null,
//       boundingBoxes: [], // Array of bounding box objects
//       selectedName: null, // The currently selected name in the sidebar
//       setPdfName: (pdfName) => set({ pdfName }),
//       setPdfUrl: (pdfUrl) => set({ pdfUrl }),
//       addBoundingBox: (boundingBox) =>
//         set((state) => ({ boundingBoxes: [...state.boundingBoxes, boundingBox] })),
//       updateBoundingBox: (id, updatedBox) =>
//         set((state) => ({
//           boundingBoxes: state.boundingBoxes.map((box) =>
//             box.id === id ? { ...box, ...updatedBox } : box
//           ),
//         })),
//       removeBoundingBox: (id) =>
//         set((state) => ({
//           boundingBoxes: state.boundingBoxes.filter((box) => box.id !== id),
//         })),
//       setSelectedName: (name) => set({ selectedName: name }),
//     }),
//     {
//       name: 'pdf-plan-store', // Name of the storage item
//     }
//   )
// );