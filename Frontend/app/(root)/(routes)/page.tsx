"use client";

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PdfViewer } from "@/components/pdf_plan/pdf_plan"; 
import { useToast } from "@/components/ui/use-toast";
import { Spinner } from '@/components/ui/spinner';
import {Configuration} from "@/lib/config"


import { usePdfPlanStore } from "@/store/PdfPlanStore";
import { Rectangle } from '@/models/pdf_plan';

export default function RootPage() {
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [legendImage, setLegendImage] = useState<File | null>(null);
  const setPdfName = usePdfPlanStore((state) => state.setPdfName);
  const setPdfUrl = usePdfPlanStore((state) => state.setPdfUrl);
  const setLegendName = usePdfPlanStore((state) => state.setLegendName);
  const setLegendUrl = usePdfPlanStore((state) => state.setLegendUrl);
  const boundingBoxes = usePdfPlanStore((state) => state.boundingBoxes);
  const setBoundingBoxes = usePdfPlanStore((state) => state.setBoundingBoxes);
  const [processingMessage, setProcessingMessage] = useState('');

  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [loading, setLoading] = useState(false);  // New loading state
  const { toast } = useToast();





  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setPdfFile(file);
      setPdfName(file.name);
      const fileUrl = URL.createObjectURL(file);
      setPdfUrl(fileUrl);
    }
  };

  const handleLegendSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setLegendImage(file);
      setLegendName(file.name);
      const fileUrl = URL.createObjectURL(file);
      setLegendUrl(fileUrl);
    }
  };

  let processingTimerId: ReturnType<typeof setTimeout>;

  const handleSubmit = async () => {

    if (pdfFile && legendImage) {
      const formData = new FormData();
      formData.append('pdffile', pdfFile);
      formData.append('legendImageFile', legendImage);
  
      setLoading(true); // Start loading
      setProcessingMessage('Processing PDF file...');
      startProcessing();
    
      try {
        const response = await fetch(
          Configuration.process_complete_plan_api,
          {
            method: 'POST',
            body: formData,
          }
        );
  
        if (response.ok) {
          const data = await response.json();
          const bounding_box_predictions = data.template_response;
   
          if (!Array.isArray(bounding_box_predictions)) {
            throw new Error('Invalid response format: template_response is not an array.');
          }
   
          const symbolTypes = [
            ...new Set(bounding_box_predictions.map((box) => `Symbol ${box.symbol_type}`)),
          ];
          
          const colors = [
            '#FF0000', // Red
            '#00FF00', // Green
            '#0000FF', // Blue
            '#FFFF00', // Yellow
            '#FF00FF', // Magenta
            '#00FFFF', // Cyan
            '#FF8C00', // Dark Orange
            '#8B00FF', // Violet
            '#FFD700', // Gold
            '#00FF7F', // Spring Green
            '#8B0000', // Dark Red
            '#006400', // Dark Green
            '#1E90FF', // Dodger Blue
            '#FF1493', // Deep Pink
            '#FF4500', // Orange Red
            '#2E8B57', // Sea Green
            '#7FFF00', // Chartreuse
            '#4682B4', // Steel Blue
            '#D2691E', // Chocolate
            '#9932CC', // Dark Orchid
          ];
          
          const symbolTypeToColor = {};
          symbolTypes.forEach((type, index) => {
            symbolTypeToColor[type] = colors[index % colors.length];
          });
   
          const dpi = Configuration.dpi;  
          const pdfJsScaleFactor = Configuration.pdfJsScaleFactor;  
          const scalingFactor = (72 * pdfJsScaleFactor) / dpi;


          const boundingBoxes: Rectangle[] = bounding_box_predictions
          .map((prediction, index) => {
            // Assuming `bbox` format: [x1, y1, width, height]
            const [x1, y1, width, height] = prediction.bbox[0];
        
            const x = x1 * scalingFactor;
            const y = y1 * scalingFactor;
            const adjustedWidth = width * scalingFactor;
            const adjustedHeight = height * scalingFactor;
        
            // Check if symbol_type is defined, even if it is 0
            const name = `Symbol ${prediction.symbol_type}`;

            const color = symbolTypeToColor[name];
            const id = index;
        
            // Return a Rectangle object
            return {
              id,
              name: name.toString(),
              x,
              y,
              width: adjustedWidth,
              height: adjustedHeight,
              color,
            } as Rectangle;
          })
          .filter((box): box is Rectangle => box !== null);

          setBoundingBoxes(boundingBoxes);
  
          setShowPdfViewer(true);
        } else {
          const errorText = await response.text();
          toast({
            variant: 'destructive',
            title: 'Error processing files:',
            description: errorText,
          });
        }
      } catch (error) {
        console.error('Error:', error);
        toast({
          variant: 'destructive',
          title: 'An error occurred while processing the files.',
          description: error.message,
        });
      } finally {
        setLoading(false); // Stop loading
        clearTimeout(processingTimerId); 
        setProcessingMessage(''); 
      }
    } else {
      toast({
        variant: 'destructive',
        title: 'Please upload both a PDF file of the construction plan and a legend image.',
      });
    }
  };
  

  const startProcessing = () => {
    clearTimeout(processingTimerId);
  

    setProcessingMessage('Getting symbols from legend...');
    
    processingTimerId = setTimeout(() => {
      setProcessingMessage('Getting symbols from PDF...');
      processingTimerId = setTimeout(() => {
        setProcessingMessage('Performing symbol matching...');
      }, 30000); 
    }, 5000); 
  };

  return (
    <>
      {!showPdfViewer ? (
        <div className="flex flex-col items-center justify-center h-[90vh] border border-gray-300 rounded-lg p-8 mx-auto overflow-hidden">
          <h1 className="text-3xl font-bold text-center mt-8 mb-4">
                Perform Quality Takeoff of Construction Plans Using AI
          </h1>
            <div className="flex flex-row space-x-1">
              <Card className="flex-1 flex flex-col items-center justify-center h-80 w-96 border border-gray-300 shadow-md rounded-lg p-6">
                <CardHeader>
                  <CardTitle>Upload PDF</CardTitle>
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileSelect}
                    className="mb-4"
                  />
                  <CardDescription>
                    Please upload a PDF of the construction plan for analysis.
                  </CardDescription>
                </CardHeader>
              </Card>
              <Card className="flex-1 flex flex-col items-center justify-center h-80 w-96 border border-gray-300 shadow-md rounded-lg p-6">
                <CardHeader>
                  <CardTitle>Upload Legend Image</CardTitle>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleLegendSelect}
                    className="mb-4"
                  />
                  <CardDescription>
                    Please upload an image of the legend for analysis.
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          {loading ? (
                  <>
                  <Spinner size="large" className="mt-4" />
                  <p className="mt-4 text-center">{processingMessage}</p>
                </>
                ) : (
                <Button className="w-20 mt-4" onClick={handleSubmit}>
                    Submit
                </Button>
            )}
        </div>
      ) : (
          <PdfViewer />
      )}
    </>
  );
}
