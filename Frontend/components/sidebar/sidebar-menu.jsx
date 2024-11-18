"use client";

import React from 'react';
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "/components/ui/scroll-area";
import PresetActions from '@/components/sidebar/menu/preset-actions';  
import { useAudioStore } from '@/store/useAudioStore';

const SidebarMenu = () => {
    const audioFiles = useAudioStore((state) => state.audioFiles);
    console.log(audioFiles)
    return (

        <ScrollArea className="h-72 w-48 rounded-md border">
                {audioFiles.map((item, index) => {
                    const { fileName,filePath} = item;  
                    const data = {
                        text: fileName.slice(0, -12),   
                        url: "/",         
                    };
                    return <PresetActions key={index} data={data} />;  
                })}
      </ScrollArea>


    );
};

export default SidebarMenu;
